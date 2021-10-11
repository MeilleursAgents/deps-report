from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from deps_report.models import Dependency, Vulnerability

logger = logging.getLogger(__name__)


class VulnerabilityCheckerBase(ABC):
    @classmethod
    @abstractmethod
    async def create(cls) -> VulnerabilityCheckerBase:
        """Create the checker instance by fetching the required data."""
        pass

    @abstractmethod
    def check_if_package_is_vulnerable(
        self,
        dependency: Dependency,
    ) -> Vulnerability | None:
        """Check if the specified dependency has a vulnerability reported."""
        pass
