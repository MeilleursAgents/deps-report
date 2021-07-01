import re
from typing import Union

from deps_report.parsers.python.pipenv import PythonPipenvParser
from deps_report.parsers.python.poetry import PythonPoetryParser

PARSERS_RULES = {
    r".*Pipfile(.lock)?$": PythonPipenvParser,
    r".*poetry.lock?$": PythonPoetryParser,
    r".*pyproject.toml?$": PythonPoetryParser,
}


def get_parser_for_file_path(
    file_path: str,
) -> Union[PythonPipenvParser, PythonPoetryParser]:
    """Get the correct dependency parser according to the filename."""
    for rule_regex, parser_class in PARSERS_RULES.items():
        if re.match(rule_regex, file_path):
            return parser_class(file_path)  # type: ignore

    raise ValueError(f"Cannot parse dependencies for {file_path}")
