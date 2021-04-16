import click
from packaging import version as version_parser
from tabulate import tabulate

from deps_report import __version__
from deps_report.parsers import get_parser_for_file_path
from deps_report.version_checkers import get_version_checker_for_parser


@click.command()
@click.argument("filename", type=click.Path(exists=True))
def main(filename: str) -> None:
    """Generate report for the state of your dependencies."""
    click.secho(f"deps-report v{__version__}", fg="green")
    click.secho(f"File is: {filename}", fg="yellow")

    parser_class = get_parser_for_file_path(filename)
    dependencies = parser_class.get_dependencies()

    click.secho(f"Found {len(dependencies)} dependencies\n", fg="yellow")

    version_checker = get_version_checker_for_parser(type(parser_class))

    # Debug
    headers = ["Dependency", "Installed version", "Latest version"]
    table = []

    with click.progressbar(
        dependencies,
        label="Fetching latest version of dependencies",
        length=len(dependencies),
    ) as bar:
        for dependency in bar:
            latest_version = version_parser.parse(
                version_checker.get_latest_version_of_dependency(dependency)
            )
            current_version = version_parser.parse(dependency.version)

            if current_version < latest_version:
                table.append([dependency.name, current_version, latest_version])

    if len(table) > 0:
        click.secho("\nOutdated dependencies found:", fg="red")
        click.echo(f'{tabulate(table, headers, tablefmt="plain")}')
    else:
        click.secho("\nNo outdated dependencies found:", fg="green")
