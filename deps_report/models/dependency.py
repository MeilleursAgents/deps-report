from dataclasses import dataclass
from typing import List

from deps_report.models.dependency_repository import DependencyRepository


@dataclass
class Dependency:
    name: str
    version: str
    repositories: List[DependencyRepository]
