from dataclasses import dataclass

from deps_report.models.dependency import Dependency

from pydantic import BaseModel

# @dataclass
class ErrorResult(BaseModel):
    dependency: Dependency
    error: str
