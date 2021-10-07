from abc import ABC, abstractmethod

from deps_report.models import Dependency


class ParserBase(ABC):
    @abstractmethod
    def get_dependencies(self) -> list[Dependency]:
        """Parse the dependency file to return a list of the dependencies."""
        pass

    @abstractmethod
    def get_runtime_version(self) -> str | None:
        """Return the runtime version according to the dependency file."""
        pass
