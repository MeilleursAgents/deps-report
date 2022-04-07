import json
import logging
import re
from datetime import date, timedelta

import aiohttp
from aiohttp.client_exceptions import ClientConnectionError, ClientError
from dateutil.parser import parse

from deps_report.models import RuntimeInformations, VerificationError
from deps_report.runtime_version_checkers import RuntimeVersionCheckerBase

logger = logging.getLogger(__name__)

PYTHON_ENDOFLIFE_DATE_API = "https://endoflife.date/api/python.json"


class PythonRuntimeVersionChecker(RuntimeVersionCheckerBase):
    async def get_runtime_informations(
        self, current_version: str
    ) -> RuntimeInformations:
        """Get informations about your project runtime according to your current version."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PYTHON_ENDOFLIFE_DATE_API) as response:
                    response.raise_for_status()
                    data = json.loads(await response.text())
        except (ClientConnectionError, ClientError):
            error_msg = "Cannot download endoflife.date data, will skip runtime version checking"
            logger.error(error_msg)
            raise VerificationError(error_msg)

        # If the current version includes a patch level, we remove it else we cannot compare it
        version_with_patch_pattern = re.compile("[0-9]\\.[0-9]+\\.[0-9]+")
        if re.match(version_with_patch_pattern, current_version):
            current_version = ".".join(current_version.split(".")[:-1])

        # Try to get informations corresponding to the current version
        current_version_informations = next(
            (
                item
                for item in data
                if current_version == item["cycle"] or current_version == item["latest"]
            ),
            None,
        )

        if current_version_informations is None:
            error_msg = "Unknown Python version, skipping runtime version checking"
            logger.error(error_msg)
            raise VerificationError(error_msg)

        latest_version_informations = data[0]
        eol_date: date = parse(current_version_informations["eol"]).date()
        return RuntimeInformations(
            name="Python",
            current_version=current_version_informations["cycle"],
            latest_version=latest_version_informations["cycle"],
            current_version_is_outdated=latest_version_informations["cycle"]
            != current_version_informations["cycle"],
            current_version_eol_date=eol_date,
            current_version_is_eol_soon=eol_date
            <= (date.today() + timedelta(days=30 * 3))
            and eol_date > date.today(),
            current_version_is_eol=eol_date < date.today(),
        )
