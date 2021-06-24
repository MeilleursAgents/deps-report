from dataclasses import dataclass

from deps_report.models.dependency_repository import DependencyRepository


@dataclass
class Dependency:
    name: str
    version: str
    repositories: list[DependencyRepository]
    transitive: bool
    for_dev: bool
