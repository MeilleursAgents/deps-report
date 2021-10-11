from typing import Type

from deps_report.parsers import PythonPipenvParser
from deps_report.parsers.python.poetry import PythonPoetryParser
from deps_report.vulnerabilities_checkers.base import VulnerabilityCheckerBase
from deps_report.vulnerabilities_checkers.python import PythonVulnerabilityChecker

VULNERABILITY_CHECKER_RULES = {
    PythonPipenvParser: PythonVulnerabilityChecker,
    PythonPoetryParser: PythonVulnerabilityChecker,
}


async def get_vulnerability_checker_for_parser(
    parser: Type,
) -> VulnerabilityCheckerBase:
    """Get the correct vulnerability checker according to dependency parser used."""
    for parser_class, vuln_checker_class in VULNERABILITY_CHECKER_RULES.items():
        if parser == parser_class:
            ret = await vuln_checker_class.create()
            return ret

    raise NotImplementedError(
        f"Checking vulnerabilities for {parser} is not implemented yet"
    )
