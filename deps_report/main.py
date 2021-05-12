import os
from typing import Any, List

import click
from packaging import version as version_parser
from pytablewriter import MarkdownTableWriter
from tabulate import tabulate

from deps_report import __version__
from deps_report.models import Dependency, VerificationError
from deps_report.models.results import ErrorResult, VersionResult, VulnerabilityResult
from deps_report.parsers import get_parser_for_file_path
from deps_report.utils.github_action import (
    get_latest_commit_hash_of_pr,
    post_github_pr_comment,
)
from deps_report.version_checkers import get_version_checker_for_parser
from deps_report.vulnerabilities_checkers import get_vulnerability_checker_for_parser


def _print_results_github_action(
    versions_results: List[VersionResult],
    vulnerabilities_results: List[VulnerabilityResult],
    errors_results: List[ErrorResult],
) -> None:

    if "GITHUB_EVENT_PATH" not in os.environ and "INPUT_GITHUB_TOKEN" not in os.environ:
        return

    msg = ""
    if len(vulnerabilities_results) > 0:
        msg += "## Vulnerable dependencies\n"
        msg += f"<details><summary> <b>{len(versions_results)}</b> dependencies have vulnerabilities 😱</summary>\n\n"
        writer = MarkdownTableWriter(
            headers=["Dependency", "Advisory", "Versions impacted"],
            value_matrix=[
                (item.dependency_name, item.advisory, item.impacted_versions)
                for item in vulnerabilities_results
            ],
        )
        msg += f"{writer.dumps()}</details>\n"

    msg += "## Outdated dependencies\n"
    if len(versions_results) > 0:
        msg += f"<details><summary> <b>{len(versions_results)}</b> outdated dependencies found 😢</summary>\n\n"
        writer = MarkdownTableWriter(
            headers=["Dependency", "Installed version", "Latest version"],
            value_matrix=[
                (item.dependency_name, item.installed_version, item.latest_version)
                for item in versions_results
            ],
        )
        msg += f"{writer.dumps()}</details>\n"
    else:
        msg += "No outdated dependencies found 🎉\n"

    if msg:
        msg = f"# **deps-report 🔍**\nCommit scanned: {get_latest_commit_hash_of_pr()[:7]}\n{msg}"
        post_github_pr_comment(msg)


def _print_results_stdout(
    versions_results: List[VersionResult],
    vulnerabilities_results: List[VulnerabilityResult],
    errors_results: List[ErrorResult],
) -> None:

    versions_headers = ["Dependency", "Installed version", "Latest version"]
    vulnerabilities_headers = ["Dependency", "Advisory", "Versions impacted"]
    errors_headers = ["Dependency", "Error"]

    if len(errors_results) > 0:
        click.secho(
            f"\nErrors while processing {len(errors_results)} dependencies:", fg="red"
        )
        errors_table = tabulate(
            [(item.dependency_name, item.error) for item in errors_results],
            errors_headers,
            tablefmt="plain",
        )
        click.echo(errors_table)

    if len(versions_results) > 0:
        click.secho("\nOutdated dependencies found:", fg="red")
        versions_table = tabulate(
            [
                (item.dependency_name, item.installed_version, item.latest_version)
                for item in versions_results
            ],
            versions_headers,
            tablefmt="plain",
        )
        click.echo(versions_table)
    else:
        click.secho("\nNo outdated dependencies found 🎉", fg="green")

    if len(vulnerabilities_results) > 0:
        click.secho("\nVulnerabilities found:", fg="red")
        vulnerabilities_table = tabulate(
            [
                (item.dependency_name, item.advisory, item.impacted_versions)
                for item in vulnerabilities_results
            ],
            vulnerabilities_headers,
            tablefmt="plain",
        )
        click.echo(
            f'{tabulate(vulnerabilities_table, vulnerabilities_headers, tablefmt="plain")}'
        )


def _process_dependencies(
    dependencies: List[Dependency], version_checker: Any, vulnerability_checker: Any
) -> None:

    versions_results: List[VersionResult] = []
    vulnerabilities_results: List[VulnerabilityResult] = []
    errors_results: List[ErrorResult] = []

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
                errors_results.append(
                    ErrorResult(
                        dependency_name=dependency.name,
                        error="Could not fetch latest version",
                    )
                )
                continue

            current_version = version_parser.parse(dependency.version)
            if current_version < latest_version:
                versions_results.append(
                    VersionResult(
                        dependency_name=dependency.name,
                        installed_version=str(current_version),
                        latest_version=str(latest_version),
                    )
                )

            # Check if current version is vulnerable
            try:
                vulnerability = vulnerability_checker.check_if_package_is_vulnerable(
                    dependency
                )
            except VerificationError:
                errors_results.append(
                    ErrorResult(
                        dependency_name=dependency.name,
                        error="Could not check for vulnerability status",
                    )
                )
            else:
                if vulnerability:
                    vulnerabilities_results.append(
                        VulnerabilityResult(
                            dependency_name=dependency.name,
                            advisory=vulnerability.advisory,
                            impacted_versions=vulnerability.versions_impacted,
                        )
                    )

    _print_results_stdout(versions_results, vulnerabilities_results, errors_results)
    _print_results_github_action(
        versions_results, vulnerabilities_results, errors_results
    )


def _get_file_path(file: str) -> str:
    ctx = click.get_current_context()
    if not file:
        click.echo(ctx.get_help())
        ctx.exit(1)
    if os.path.isfile(file):
        return file

    # Look if exist in github action path
    if not os.path.isfile(file) and "GITHUB_WORKSPACE" in os.environ:
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
