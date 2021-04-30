import logging
from typing import Optional

import requests
from packaging.specifiers import SpecifierSet
from requests import HTTPError

from deps_report.models import Dependency, VerificationError, Vulnerability

logger = logging.getLogger(__name__)


DATABASE_URL = (
    "https://raw.githubusercontent.com/pyupio/safety-db/master/data/insecure_full.json"
)


class PythonVulnerabilityChecker:
    def __init__(self) -> None:
        """Init the checker instance with the required data."""
        try:
            json_data = requests.get(DATABASE_URL)
            json_data.raise_for_status()
        except HTTPError:
            logger.error(
                "Cannot download safety-db database, will skip vulnerabilities checking"
            )
            self.data = None
        else:
            self.data = json_data.json()

    def check_if_package_is_vulnerable(
        self,
        dependency: Dependency,
    ) -> Optional[Vulnerability]:
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
