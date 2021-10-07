from typing import Type

from deps_report.parsers import PythonPipenvParser
from deps_report.parsers.python.poetry import PythonPoetryParser
from deps_report.runtime_version_checkers.base import RuntimeVersionCheckerBase
from deps_report.runtime_version_checkers.python import PythonRuntimeVersionChecker

VERSION_CHECKER_RULES = {
    PythonPipenvParser: PythonRuntimeVersionChecker,
    PythonPoetryParser: PythonRuntimeVersionChecker,
}


def get_runtime_version_checker_for_parser(parser: Type) -> RuntimeVersionCheckerBase:
    """Get the correct runtime version checker according to dependency parser used."""
    for parser_class, version_checker_class in VERSION_CHECKER_RULES.items():
        if parser == parser_class:
            return version_checker_class()

    raise NotImplementedError(f"Checking versions for {parser} is not implemented yet")
