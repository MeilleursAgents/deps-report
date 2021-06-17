from dataclasses import dataclass
from deps_report.models.dependency import Dependency


@dataclass
class ErrorResult:
    dependency: Dependency
    error: str
