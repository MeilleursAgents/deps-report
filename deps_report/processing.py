from packaging import version as version_parser

from deps_report.dependencies_version_checkers import DependenciesVersionCheckerBase
from deps_report.models import Dependency, VerificationError
from deps_report.models.results import ErrorResult, VersionResult, VulnerabilityResult
from deps_report.vulnerabilities_checkers import VulnerabilityCheckerBase


async def process_dependency(
    version_checker: DependenciesVersionCheckerBase,
    vulnerability_checker: VulnerabilityCheckerBase,
    dependency: Dependency,
) -> tuple[VersionResult | None, VulnerabilityResult | None, list[ErrorResult]]:
    """For a given dependencies and the associated checker instances, check if the version is the latest and if there is any vulnerabilities in the installed version."""
    errors_results = []
    version_result = None
    vulnerability_result = None

    try:
        latest_version = version_parser.parse(
            await version_checker.get_latest_version_of_dependency(dependency)
        )
    except VerificationError:
        errors_results.append(
            ErrorResult(
                dependency=dependency,
                error="Could not fetch latest version",
            )
        )
        return version_result, vulnerability_result, errors_results

    current_version = version_parser.parse(dependency.version)
    if current_version < latest_version:
        version_result = VersionResult(
            dependency=dependency,
            installed_version=str(current_version),
            latest_version=str(latest_version),
        )

    # Check if current version is vulnerable
    try:
        vulnerability = vulnerability_checker.check_if_package_is_vulnerable(dependency)
    except VerificationError:
        errors_results.append(
            ErrorResult(
                dependency=dependency,
                error="Could not check for vulnerability status",
            )
        )
    else:
        if vulnerability:
            vulnerability_result = VulnerabilityResult(
                dependency=dependency,
                advisory=vulnerability.advisory,
                impacted_versions=vulnerability.versions_impacted,
            )

    return version_result, vulnerability_result, errors_results
