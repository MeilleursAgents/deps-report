from typing import Type, Union

from deps_report.parsers import PythonPipenvParser
from deps_report.vulnerabilities_checkers.python import PythonVulnerabilityChecker

__all__ = [
    PythonVulnerabilityChecker.__name__,
]

VULNERABILITY_CHECKER_RULES = {PythonPipenvParser: PythonVulnerabilityChecker}


def get_vulnerability_checker_for_parser(
    parser: Type,
) -> Union[PythonVulnerabilityChecker]:
    """Get the correct vulnerability checker according to dependency parser used."""
    for parser_class, version_checker_class in VULNERABILITY_CHECKER_RULES.items():
        if parser == parser_class:
            return version_checker_class()

    raise NotImplementedError(
        f"Checking vulnerabilities for {parser} is not implemented yet"
    )
