import os
import sys
from typing import Any, List

import click
from packaging import version as version_parser
from tabulate import tabulate

from deps_report import __version__
from deps_report.models import Dependency, VerificationError
from deps_report.parsers import get_parser_for_file_path
from deps_report.version_checkers import get_version_checker_for_parser
from deps_report.vulnerabilities_checkers import get_vulnerability_checker_for_parser


def _print_results(
    results_headers: List[str],
    results_table: List,
    errors_headers: List[str],
    errors_table: List,
    vulnerabilities_headers: List[str],
    vulnerabilities_table: List,
) -> None:
    if len(errors_table) > 0:
        click.secho(
            f"\nErrors while processing {len(errors_table)} dependencies:", fg="red"
        )
        click.echo(f'{tabulate(errors_table, errors_headers, tablefmt="plain")}')

    if len(results_table) > 0:
        click.secho("\nOutdated dependencies found:", fg="red")
        click.echo(f'{tabulate(results_table, results_headers, tablefmt="plain")}')
    else:
        click.secho("\nNo outdated dependencies found:", fg="green")

    if len(vulnerabilities_table) > 0:
        click.secho("\nVulnerabilities found:", fg="red")
        click.echo(
            f'{tabulate(vulnerabilities_table, vulnerabilities_headers, tablefmt="plain")}'
        )


def _process_dependencies(
    dependencies: List[Dependency], version_checker: Any, vulnerability_checker: Any
) -> None:
    results_headers = ["Dependency", "Installed version", "Latest version"]
    results_table = []

    vulnerabilities_headers = ["Dependency", "Advisory", "Versions impacted"]
    vulnerabilities_table = []

    errors_headers = ["Dependency", "Error"]
    errors_table = []

    with click.progressbar(
        dependencies,
        label="Fetching latest version of dependencies",
        length=len(dependencies),
    ) as bar:
        for dependency in bar:

            # Check latest version
            try:
                latest_version = version_parser.parse(
                    version_checker.get_latest_version_of_dependency(dependency)
                )
            except VerificationError:
                errors_table.append([dependency.name, "Could not fetch latest version"])
                continue

            current_version = version_parser.parse(dependency.version)
            if current_version < latest_version:
                results_table.append([dependency.name, current_version, latest_version])

            # Check if current version is vulnerable
            try:
                vulnerability = vulnerability_checker.check_if_package_is_vulnerable(
                    dependency
                )
            except VerificationError:
                errors_table.append(
                    [dependency.name, "Could not check for vulnerability status"]
                )
            else:
                if vulnerability:
                    vulnerabilities_table.append(
                        [
                            dependency.name,
                            vulnerability.advisory,
                            vulnerability.versions_impacted,
                        ]
                    )

    _print_results(
        results_headers,
        results_table,
        errors_headers,
        errors_table,
        vulnerabilities_headers,
        vulnerabilities_table,
    )


def _get_file_path(file: str) -> str:
    ctx = click.get_current_context()
    if not file:
        click.echo(ctx.get_help())
        ctx.exit(1)
    if os.path.isfile(file):
        return file

    # Look if exist in github action path
    if not os.path.isfile(file) and 'GITHUB_WORKSPACE' in os.environ:
        github_action_path = f"{os.environ['GITHUB_WORKSPACE']}/{file}"
        if os.path.isfile(github_action_path):
            return github_action_path

    ctx.fail(f"file {file} not found")
    ctx.exit(1)


@click.command()
@click.argument(
    "file",
    type=click.Path(),
    default=lambda: os.environ.get("INPUT_FILE", ""),
)
def main(file: str) -> None:
    """Generate report for the state of your dependencies."""

    click.secho(f"deps-report v{__version__}", fg="green")
    file = _get_file_path(file)
    click.secho(f"File is: {file}", fg="yellow")

    parser_class = get_parser_for_file_path(file)
    dependencies = parser_class.get_dependencies()

    click.secho(f"Found {len(dependencies)} dependencies\n", fg="yellow")

    version_checker = get_version_checker_for_parser(type(parser_class))
    vulnerability_checker = get_vulnerability_checker_for_parser(type(parser_class))

    _process_dependencies(dependencies, version_checker, vulnerability_checker)
