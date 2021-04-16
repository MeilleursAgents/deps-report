import re
from typing import Union

from deps_report.parsers.python import PipenvParser

PARSERS_RULES = {r"Pipfile(.lock)?$": PipenvParser}


def get_parser_for_file_path(file_path: str) -> Union[PipenvParser]:
    """Get the correct dependency parser according to the filename."""
    for rule_regex, parser_class in PARSERS_RULES.items():
        if re.match(rule_regex, file_path):
            return parser_class(file_path)

    raise ValueError(f"Cannot parse dependencies for {file_path}")
