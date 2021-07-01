from typing import Type, Union

from deps_report.parsers import PythonPipenvParser
from deps_report.parsers.python.poetry import PythonPoetryParser
from deps_report.version_checkers.python import PythonVersionChecker

VERSION_CHECKER_RULES = {
    PythonPipenvParser: PythonVersionChecker,
    PythonPoetryParser: PythonVersionChecker,
}


def get_version_checker_for_parser(parser: Type) -> Union[PythonVersionChecker]:
    """Get the correct version checker according to dependency parser used."""
    for parser_class, version_checker_class in VERSION_CHECKER_RULES.items():
        if parser == parser_class:
            return version_checker_class()

    raise NotImplementedError(f"Checking versions for {parser} is not implemented yet")
