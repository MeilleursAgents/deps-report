from dataclasses import dataclass


@dataclass
class DependencyRepository:
    name: str
    url: str
