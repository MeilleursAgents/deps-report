from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel

# @dataclass
class RuntimeInformations(BaseModel):
    name: str
    current_version: str
    latest_version: str
    current_version_is_outdated: bool
    current_version_eol_date: date
    current_version_is_eol_soon: bool
    current_version_is_eol: bool
