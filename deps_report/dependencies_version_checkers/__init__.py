from typing import Type

from deps_report.dependencies_version_checkers.base import (
    DependenciesVersionCheckerBase,
)
from deps_report.dependencies_version_checkers.python import (
    PythonDependenciesVersionChecker,
)
from deps_report.parsers import PythonPipenvParser
from deps_report.parsers.python.poetry import PythonPoetryParser

VERSION_CHECKER_RULES = {
    PythonPipenvParser: PythonDependenciesVersionChecker,
    PythonPoetryParser: PythonDependenciesVersionChecker,
}


def get_dependencies_version_checker_for_parser(
    parser: Type,
) -> DependenciesVersionCheckerBase:
    """Get the correct dependencies version checker according to dependency parser used."""
    for parser_class, version_checker_class in VERSION_CHECKER_RULES.items():
        if parser == parser_class:
            return version_checker_class()

    raise NotImplementedError(f"Checking versions for {parser} is not implemented yet")
