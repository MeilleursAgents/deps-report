import logging
from abc import ABC, abstractmethod

from deps_report.models import RuntimeInformations

logger = logging.getLogger(__name__)


class RuntimeVersionCheckerBase(ABC):
    @abstractmethod
    async def get_runtime_informations(
        self, current_version: str
    ) -> RuntimeInformations:
        """Get informations about your project runtime according to your current version."""
        pass
