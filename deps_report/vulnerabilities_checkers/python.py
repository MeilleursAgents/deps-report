from __future__ import annotations

import json
import logging

import aiohttp
from aiohttp.client_exceptions import ClientConnectionError, ClientError
from packaging.specifiers import SpecifierSet

from deps_report.models import Dependency, VerificationError, Vulnerability
from deps_report.vulnerabilities_checkers import VulnerabilityCheckerBase

logger = logging.getLogger(__name__)


DATABASE_URL = (
    "https://raw.githubusercontent.com/pyupio/safety-db/master/data/insecure_full.json"
)


class PythonVulnerabilityChecker(VulnerabilityCheckerBase):
    def __init__(self, vulnerabilities_data: dict | None) -> None:
        """Initialize the Python vulnerability checker."""
        self.data = vulnerabilities_data

    @classmethod
    async def create(cls) -> PythonVulnerabilityChecker:
        """Create the checker instance by fetching the required data."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(DATABASE_URL) as response:
                    response.raise_for_status()
                    data = json.loads(await response.text())
        except (ClientConnectionError, ClientError):
            logger.error(
                "Cannot download safety-db database, will skip vulnerabilities checking"
            )
            data = None

        return PythonVulnerabilityChecker(data)

    def check_if_package_is_vulnerable(
        self,
        dependency: Dependency,
    ) -> Vulnerability | None:
        """Check if the specified dependency has a vulnerability reported."""
        if not self.data:
            raise VerificationError(
                "Cannot check vulnerability status, error when downloading database"
            )

        database_entry = self.data.get(dependency.name)
        if database_entry is None:
            return None

        for vulnerability_entry in database_entry:
            constraint = vulnerability_entry["v"]
            specifier_set = SpecifierSet(constraint)

            if specifier_set.contains(dependency.version):
                return Vulnerability(
                    advisory=vulnerability_entry["advisory"],
                    cve=vulnerability_entry.get("cve"),
                    versions_impacted=constraint,
                )

        return None
