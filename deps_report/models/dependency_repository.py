from dataclasses import dataclass
from pydantic import BaseModel


class DependencyRepository(BaseModel):
    name: str
    url: str
