from dataclasses import dataclass

from deps_report.models.dependency_repository import DependencyRepository

from pydantic import BaseModel
# @dataclass
class Dependency(BaseModel):
    name: str
    version: str
    repositories: list[DependencyRepository]
    transitive: bool
    for_dev: bool
