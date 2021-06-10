import logging

import requests
from bs4 import BeautifulSoup
from packaging import version as version_parser
from requests import HTTPError

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

    def _get_latest_version_from_repository(self, url: str) -> str:
        simple_page = requests.get(url)

        if simple_page.status_code == 404:
            raise ValueError("Dependency doesn't exist on repository")

        simple_page.raise_for_status()

        for filename in self._get_filenames_from_simple_page(simple_page.text):
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

    def get_latest_version_of_dependency(self, dependency: Dependency) -> str:
        """Get the latest version available of a specified dependency."""
        for repository in dependency.repositories:
            url = f"{repository.url}/{dependency.name}"
            try:
                version = self._get_latest_version_from_repository(url)
            except ValueError:
                continue
            except HTTPError:
                logger.info("Error while fetching repository informations")
            else:
                return version

        raise VerificationError(f"Cannot check version for {dependency.name}")
