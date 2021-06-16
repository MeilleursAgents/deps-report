import logging

import aiohttp
from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientConnectionError, ClientError
from bs4 import BeautifulSoup
from packaging import version as version_parser

from deps_report.models import Dependency, VerificationError

logger = logging.getLogger(__name__)


class PythonVersionChecker:
    def _get_version_from_wheel_filename(self, filename: str) -> str:
        return filename.split("-")[1]

    def _get_version_from_source_filename(self, filename: str) -> str:
        version_with_extension = filename.split("-")[-1]
        return version_with_extension.replace(".zip", "").replace(".tar.gz", "")

    def _get_filenames_from_simple_page(self, page_text: str) -> list[str]:
        soup = BeautifulSoup(page_text, features="html.parser")
        filenames = [item.text for item in soup.find_all("a")]
        filenames.reverse()
        return filenames

    async def _get_latest_version_from_repository(
        self, session: ClientSession, url: str
    ) -> str:
        async with session.get(url) as response:
            if response.status == 404:
                raise ValueError("Dependency doesn't exist on repository")

            response.raise_for_status()

            page_content = await response.text()

        for filename in self._get_filenames_from_simple_page(page_content):
            if filename.endswith((".egg", ".whl")):
                version = self._get_version_from_wheel_filename(filename)
            elif filename.endswith((".tar.gz", ".zip")):
                version = self._get_version_from_source_filename(filename)
            else:
                raise NotImplementedError(f"Cannot check version for {filename}")

            try:
                parsed_version = version_parser.parse(version)
            except ValueError:
                continue

            if not parsed_version.is_prerelease:
                return version

        raise ValueError(f"Cannot check version for {url}")

    async def get_latest_version_of_dependency(self, dependency: Dependency) -> str:
        """Get the latest version available of a specified dependency."""
        async with aiohttp.ClientSession() as session:
            for repository in dependency.repositories:
                url = f"{repository.url}/{dependency.name}"
                try:
                    version = await self._get_latest_version_from_repository(
                        session, url
                    )
                except ValueError:
                    continue
                except (ClientConnectionError, ClientError):
                    logger.info("Error while fetching repository informations")
                else:
                    return version

        raise VerificationError(f"Cannot check version for {dependency.name}")
