import click
from tabulate import tabulate

from deps_report.models.results import ErrorResult, VersionResult, VulnerabilityResult
from deps_report.models.runtime_informations import RuntimeInformations
from deps_report.utils.output.common import (
    get_dependencies_with_outdated_major,
    get_display_output_for_dependency,
)


def print_results_stdout(
    versions_results: list[VersionResult],
    vulnerabilities_results: list[VulnerabilityResult],
    errors_results: list[ErrorResult],
    runtime_informations: RuntimeInformations | None,
) -> None:
    """Print results as tables on stdout."""
    versions_headers = ["Dependency", "Installed version", "Latest version"]
    vulnerabilities_headers = ["Dependency", "Advisory", "Versions impacted"]
    errors_headers = ["Dependency", "Error"]

    if runtime_informations and runtime_informations.current_version_is_outdated:
        click.secho(
            f"\n{runtime_informations.name} version {runtime_informations.current_version} is used by your project but the latest version is {runtime_informations.latest_version}.",
            fg="yellow",
        )
        if runtime_informations.current_version_is_eol_soon:
            click.secho(
                f"Your {runtime_informations.name} version reaches EOL date on {runtime_informations.current_version_eol_date}, you should upgrade !",
                fg="red",
            )
        elif runtime_informations.current_version_is_eol:
            click.secho(
                f"Your {runtime_informations.name} version reached EOL date on {runtime_informations.current_version_eol_date}, you should upgrade !",
                fg="red",
            )

    if len(vulnerabilities_results) > 0:
        click.secho(
            f"\n{len(vulnerabilities_results)} vulnerable dependencies found:", fg="red"
        )
        vulnerabilities_table = tabulate(
            [
                (
                    get_display_output_for_dependency(item.dependency),
                    item.advisory,
                    item.impacted_versions,
                )
                for item in vulnerabilities_results
            ],
            vulnerabilities_headers,
            tablefmt="plain",
        )
        click.echo(vulnerabilities_table)

    if len(versions_results) > 0:
        outdated_major = get_dependencies_with_outdated_major(versions_results)
        click.secho(
            f"\n{len(versions_results)} outdated dependencies found (including {len(outdated_major)} outdated major versions):",
            fg="red",
        )
        versions_table = tabulate(
            [
                (
                    get_display_output_for_dependency(item.dependency),
                    item.installed_version,
                    item.latest_version,
                )
                for item in versions_results
            ],
            versions_headers,
            tablefmt="plain",
        )
        click.echo(versions_table)
    else:
        click.secho("\nNo outdated dependencies found 🎉", fg="green")

    if len(errors_results) > 0:
        click.secho(f"\n{len(errors_results)} errors:", fg="red")
        errors_table = tabulate(
            [
                (get_display_output_for_dependency(item.dependency), item.error)
                for item in errors_results
            ],
            errors_headers,
            tablefmt="plain",
        )
        click.echo(errors_table)
