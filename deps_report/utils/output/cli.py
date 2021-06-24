import click
from tabulate import tabulate

from deps_report.models.results import ErrorResult, VersionResult, VulnerabilityResult
from deps_report.utils.output.common import get_display_output_for_dependency


def print_results_stdout(
    versions_results: list[VersionResult],
    vulnerabilities_results: list[VulnerabilityResult],
    errors_results: list[ErrorResult],
) -> None:
    """Print results as tables on stdout."""
    versions_headers = ["Dependency", "Installed version", "Latest version"]
    vulnerabilities_headers = ["Dependency", "Advisory", "Versions impacted"]
    errors_headers = ["Dependency", "Error"]

    if len(vulnerabilities_results) > 0:
        click.secho("\nVulnerabilities found:", fg="red")
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
        click.secho("\nOutdated dependencies found:", fg="red")
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
