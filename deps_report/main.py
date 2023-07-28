import asyncio
import itertools
import json
import os
import sys
from csv import DictReader
from pathlib import Path

import click

from deps_report import __version__
from deps_report.dependencies_version_checkers import (
    get_dependencies_version_checker_for_parser,
)
from deps_report.dependencies_version_checkers.base import (
    DependenciesVersionCheckerBase,
)
from deps_report.models import Dependency, VerificationError
from deps_report.models.results import ErrorResult, VersionResult, VulnerabilityResult
from deps_report.models.runtime_informations import RuntimeInformations
from deps_report.parsers import get_parser_for_file_path
from deps_report.processing import process_dependency
from deps_report.runtime_version_checkers import get_runtime_version_checker_for_parser
from deps_report.utils.asynchronous import coroutine
from deps_report.utils.output.cli import print_results_stdout
from deps_report.utils.output.github_action import send_github_pr_comment_with_results
from deps_report.vulnerabilities_checkers import get_vulnerability_checker_for_parser
from deps_report.vulnerabilities_checkers.base import VulnerabilityCheckerBase


async def _process_project(
    dependencies: list[Dependency],
    dependencies_version_checker: DependenciesVersionCheckerBase,
    vulnerability_checker: VulnerabilityCheckerBase,
    runtimes_informations: RuntimeInformations | None,
) -> None:
    versions_results: list[VersionResult] = []
    vulnerabilities_results: list[VulnerabilityResult] = []
    errors_results: list[ErrorResult] = []

    click.echo("Processing dependencies...")
    results = await asyncio.gather(
        *[
            process_dependency(
                dependencies_version_checker, vulnerability_checker, dependency
            )
            for dependency in dependencies
        ]
    )

    versions_results, vulnerabilities_results, errors_results = map(list, zip(*results))  # type: ignore
    errors_results = list(itertools.chain(*errors_results))  # type: ignore

    # Filter empty results
    versions_results = list(filter(None, versions_results))
    vulnerabilities_results = list(filter(None, vulnerabilities_results))

    # Print in stdout and send github comment if on Github
    print_results_stdout(
        versions_results, vulnerabilities_results, errors_results, runtimes_informations
    )
    send_github_pr_comment_with_results(
        versions_results, vulnerabilities_results, errors_results, runtimes_informations
    )


async def _process_project_json(
    dependencies: list[Dependency],
    dependencies_version_checker: DependenciesVersionCheckerBase,
    vulnerability_checker: VulnerabilityCheckerBase,
    runtimes_informations: RuntimeInformations | None,
    output_file: Path,
) -> None:
    versions_results: list[VersionResult] = []
    vulnerabilities_results: list[VulnerabilityResult] = []
    errors_results: list[ErrorResult] = []

    click.echo("Processing dependencies...")
    results = await asyncio.gather(
        *[
            process_dependency(
                dependencies_version_checker, vulnerability_checker, dependency
            )
            for dependency in dependencies
        ]
    )

    versions_results, vulnerabilities_results, errors_results = map(list, zip(*results))  # type: ignore
    errors_results = list(itertools.chain(*errors_results))  # type: ignore

    # Filter empty results
    versions_results = list(filter(None, versions_results))
    vulnerabilities_results = list(filter(None, vulnerabilities_results))

    result_dict = {
        "version_results": [v.dict() for v in versions_results],
        "vulnerabilities_result": [v.dict() for v in vulnerabilities_results],
        "errors_results": [v.dict() for v in errors_results],
        "runtime_informations": runtimes_informations.dict(),
    }
    # FIXME : quickfix to avoid not serializable date error
    result_dict["runtime_informations"]["current_version_eol_date"] = result_dict[
        "runtime_informations"
    ]["current_version_eol_date"].isoformat()

    with output_file.open("w") as fp:
        json.dump(result_dict, fp)

    click.echo(f"Results saved in {str(output_file)}")
    # Print in stdout and send github comment if on Github
    print_results_stdout(
        versions_results, vulnerabilities_results, errors_results, runtimes_informations
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
    runtime_version = parser_class.get_runtime_version()

    click.secho(f"Found {len(dependencies)} dependencies\n", fg="yellow")

    dependencies_version_checker = get_dependencies_version_checker_for_parser(
        type(parser_class)
    )
    vulnerability_checker = await get_vulnerability_checker_for_parser(
        type(parser_class)
    )

    runtime_informations: RuntimeInformations | None = None
    if runtime_version:
        try:
            runtime_informations = await get_runtime_version_checker_for_parser(
                type(parser_class)
            ).get_runtime_informations(runtime_version)
        except VerificationError:
            runtime_informations = None

    await _process_project_json(
        dependencies,
        dependencies_version_checker,
        vulnerability_checker,
        runtime_informations,
    )


async def main_no_click(file, output_file):
    click.secho(f"deps-report v{__version__}", fg="green")
    click.secho(f"File is: {file}", fg="yellow")

    parser_class = get_parser_for_file_path(file)
    dependencies = parser_class.get_dependencies()
    runtime_version = parser_class.get_runtime_version()

    click.secho(f"Found {len(dependencies)} dependencies\n", fg="yellow")

    dependencies_version_checker = get_dependencies_version_checker_for_parser(
        type(parser_class)
    )
    vulnerability_checker = await get_vulnerability_checker_for_parser(
        type(parser_class)
    )

    runtime_informations: RuntimeInformations | None = None
    if runtime_version:
        try:
            runtime_informations = await get_runtime_version_checker_for_parser(
                type(parser_class)
            ).get_runtime_informations(runtime_version)
        except VerificationError:
            runtime_informations = None

    await _process_project_json(
        dependencies,
        dependencies_version_checker,
        vulnerability_checker,
        runtime_informations,
        output_file,
    )


def do_all(ma_apps_path):
    loop = asyncio.new_event_loop()
    with ma_apps_path.open("r") as fp:
        reader = DictReader(fp)
        for row in reader:
            if row.get("pipfile.lock"):
                app_name = row.get("full_name").lower()
                click.echo(f"{app_name} found pipfile.lock")
                pipfile_lock_path = ma_apps_path.parent.joinpath(
                    Path(row.get("pipfile.lock"))
                )
                output_file = pipfile_lock_path.with_name("out.json")
                click.echo(f"output is : {str(output_file)}")
                if not output_file.exists():
                    if app_name not in [
                        "meilleursagents/de-indices",
                        "meilleursagents/e2e-api-data",
                    ]:
                        loop.run_until_complete(
                            main_no_click(str(pipfile_lock_path), output_file)
                        )
                    else:
                        click.echo(f"skipping {app_name} not supported")
                else:
                    click.echo(f"skipping {app_name} output already exists")
            else:
                click.echo(f"{row.get('full_name')} does not have pipfile.lock")


if __name__ == "__main__":
    ma_apps_path = Path("ma-repos.csv")
    do_all(ma_apps_path)
