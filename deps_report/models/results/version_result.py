from dataclasses import dataclass


@dataclass
class VersionResult:
    dependency_name: str
    installed_version: str
    latest_version: str
