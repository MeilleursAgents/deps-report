import asyncio
import itertools
import os
from typing import Any, Optional

import click
from packaging import version as version_parser

from deps_report import __version__
from deps_report.models import Dependency, VerificationError
from deps_report.models.results import ErrorResult, VersionResult, VulnerabilityResult
from deps_report.parsers import get_parser_for_file_path
from deps_report.utils.asynchronous import coroutine
from deps_report.utils.cli import print_results_stdout
from deps_report.utils.github_action import send_github_pr_comment_with_results
from deps_report.version_checkers import get_version_checker_for_parser
from deps_report.vulnerabilities_checkers import get_vulnerability_checker_for_parser


async def _process_dependency(
    version_checker: Any, vulnerability_checker: Any, dependency: Dependency
) -> tuple[Optional[VersionResult], Optional[VulnerabilityResult], list[ErrorResult]]:
    await asyncio.sleep(0.001)

    errors_results = []
    version_result = None
    vulnerability_result = None

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
        return version_result, vulnerability_result, errors_results

    current_version = version_parser.parse(dependency.version)
    if current_version < latest_version:
        version_result = VersionResult(
            dependency_name=dependency.name,
            installed_version=str(current_version),
            latest_version=str(latest_version),
        )

    # Check if current version is vulnerable
    try:
        vulnerability = vulnerability_checker.check_if_package_is_vulnerable(dependency)
    except VerificationError:
        errors_results.append(
            ErrorResult(
                dependency_name=dependency.name,
                error="Could not check for vulnerability status",
            )
        )
    else:
        if vulnerability:
            vulnerability_result = VulnerabilityResult(
                dependency_name=dependency.name,
                advisory=vulnerability.advisory,
                impacted_versions=vulnerability.versions_impacted,
            )

    return version_result, vulnerability_result, errors_results


async def _process_dependencies(
    dependencies: list[Dependency], version_checker: Any, vulnerability_checker: Any
) -> None:
    versions_results: list[VersionResult] = []
    vulnerabilities_results: list[VulnerabilityResult] = []
    errors_results: list[ErrorResult] = []

    click.echo("Processing dependencies...")
    results = await asyncio.gather(
        *[
            _process_dependency(version_checker, vulnerability_checker, dependency)
            for dependency in dependencies
        ]
    )

    versions_results, vulnerabilities_results, errors_results = map(list, zip(*results))  # type: ignore
    versions_results = list(filter(None, versions_results))
    vulnerabilities_results = list(filter(None, vulnerabilities_results))
    errors_results = list(itertools.chain(*errors_results))  # type: ignore

    print_results_stdout(versions_results, vulnerabilities_results, errors_results)
    send_github_pr_comment_with_results(
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


@click.command()
@click.argument(
    "file",
    type=click.Path(),
    default=lambda: os.environ.get("INPUT_FILE", ""),
)
@coroutine
async def main(file: str) -> None:
    """Generate report for the state of your dependencies."""
    click.secho(f"deps-report v{__version__}", fg="green")
    file = _get_file_path(file)
    click.secho(f"File is: {file}", fg="yellow")

    parser_class = get_parser_for_file_path(file)
    dependencies = parser_class.get_dependencies()

    click.secho(f"Found {len(dependencies)} dependencies\n", fg="yellow")

    version_checker = get_version_checker_for_parser(type(parser_class))
    vulnerability_checker = get_vulnerability_checker_for_parser(type(parser_class))

    await _process_dependencies(dependencies, version_checker, vulnerability_checker)
