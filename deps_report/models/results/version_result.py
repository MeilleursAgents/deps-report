from dataclasses import dataclass

from deps_report.models.dependency import Dependency


@dataclass
class VersionResult:
    dependency: Dependency
    installed_version: str
    latest_version: str
