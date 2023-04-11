from dataclasses import dataclass
from packaging import version as version_parser
from deps_report.models.dependency import Dependency

from pydantic import BaseModel

# @dataclass
class VersionResult(BaseModel):
    dependency: Dependency
    installed_version: str
    latest_version: str

    def is_outdated_major(self):
        latest_version = version_parser.parse(self.latest_version)
        installed_version = version_parser.parse(self.installed_version)

        if latest_version.major > installed_version.major:
            return True
        return False
