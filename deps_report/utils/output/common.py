from packaging import version as version_parser

from deps_report.models import Dependency
from deps_report.models.results import VersionResult


def get_display_output_for_dependency(dependency: Dependency) -> str:
    """Get display name for dependency with some details (transitive, dev-only...)."""
    properties = []
    if dependency.for_dev:
        properties.append("dev")
    if dependency.transitive:
        properties.append("transitive")

    if len(properties) == 0:
        return dependency.name

    return f"{dependency.name} ({','.join(properties)})"


def get_number_of_dependencies_with_outdated_major(results: list[VersionResult]) -> int:
    """Get the number of dependencies with outdated major versions."""
    count = 0

    for result in results:
        latest_version = version_parser.parse(result.latest_version)
        installed_version = version_parser.parse(result.installed_version)

        if isinstance(latest_version, version_parser.LegacyVersion) or isinstance(
            installed_version, version_parser.LegacyVersion
        ):
            continue

        if latest_version.major > installed_version.major:
            count += 1

    return count
