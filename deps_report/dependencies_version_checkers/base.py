import logging
from abc import ABC, abstractmethod

from deps_report.models import Dependency

logger = logging.getLogger(__name__)


class DependenciesVersionCheckerBase(ABC):
    @abstractmethod
    async def get_latest_version_of_dependency(self, dependency: Dependency) -> str:
        """Get the latest version available of a specified dependency."""
        pass
