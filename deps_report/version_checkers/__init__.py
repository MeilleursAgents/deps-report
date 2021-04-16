from typing import Type, Union

from deps_report.parsers.python import PipenvParser
from deps_report.version_checkers.python import SimpleVersionChecker

VERSION_CHECKER_RULES = {PipenvParser: SimpleVersionChecker}


def get_version_checker_for_parser(parser: Type) -> Union[SimpleVersionChecker]:
    """Get the correct version checker according to dependency parser used."""
    for parser_class, version_checker_class in VERSION_CHECKER_RULES.items():
        if parser == parser_class:
            return version_checker_class()

    raise NotImplementedError(f"Checking versions for {parser} is not implemented yet")
