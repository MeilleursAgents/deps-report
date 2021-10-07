import json
import logging
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

        current_version_informations = next(
            (
                item
                for item in data
                if current_version == item["cycle"] or current_version == item["latest"]
            ),
            None,
        )
        latest_version_informations = data[0]

        if current_version_informations is None:
            error_msg = "Unknown Python version, skipping runtime version checking"
            logger.error(error_msg)
            raise VerificationError(error_msg)

        eol_date: date = parse(current_version_informations["eol"]).date()

        return RuntimeInformations(
            name="Python",
            current_version=current_version_informations["cycle"],
            latest_version=latest_version_informations["cycle"],
            current_version_is_outdated=latest_version_informations["cycle"]
            != current_version_informations["cycle"],
            current_version_eol_date=eol_date,
            current_version_is_eol_soon=eol_date
            <= (date.today() - timedelta(days=30 * 3)),
        )
