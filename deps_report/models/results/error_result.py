from dataclasses import dataclass


@dataclass
class ErrorResult:
    dependency_name: str
    error: str
