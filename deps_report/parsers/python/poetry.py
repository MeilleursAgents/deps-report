import os
from typing import Any

import toml

from deps_report.models import Dependency, DependencyRepository
from deps_report.parsers import ParserBase
from deps_report.parsers.python.common import DEFAULT_REPOSITORY


class PythonPoetryParser(ParserBase):
    def __init__(self, given_file_path: str) -> None:
        """Create the parser for the given path."""
        self.pyproject_file_path, self.poetry_lock_file_path = self._get_file_paths(
            given_file_path
        )

    def _get_file_paths(self, given_file_path: str) -> tuple[str, str]:
        """Get a tuple containing the file path for pyproject.toml and the file path for poetry.lock."""
        given_path, given_filename = os.path.split(given_file_path)

        if given_filename == "poetry.lock":
            return os.path.join(given_path, "pyproject.toml"), given_file_path
        elif given_filename == "pyproject.toml":
            return (
                given_file_path,
                os.path.join(given_path, "poetry.lock"),
            )

        raise ValueError(
            "Invalid file path provided: you need to specify the path to your pyproject.toml or poetry.lock file"
        )

    def _get_repositories(self) -> dict[str, DependencyRepository]:
        return {"pypi": DEFAULT_REPOSITORY}

    def _is_transitive_dependency(
        self, pyproject_file_content: Any, dependency_name: str
    ) -> bool:
        """Check if a dependency is transitive by looking if it's present in the Pipfile."""
        return (
            dependency_name
            not in pyproject_file_content["tool"]["poetry"]["dependencies"]
            and dependency_name
            not in pyproject_file_content["tool"]["poetry"]["dev-dependencies"]
        )

    def get_dependencies(self) -> list[Dependency]:
        """Parse the poetry.lock file to return a list of the dependencies."""
        with open(self.poetry_lock_file_path, "r") as lock_file:
            lock_file_content = toml.load(lock_file)

        with open(self.pyproject_file_path, "r") as pyproject_file_path:
            pyproject_file_content = toml.load(pyproject_file_path)

        repositories = self._get_repositories()

        dependencies: list[Dependency] = []
        for package in lock_file_content["package"]:
            name = package["name"]
            dependencies.append(
                Dependency(
                    name=name,
                    version=package["version"],
                    for_dev=package["category"] == "dev",
                    repositories=[repositories["pypi"]],
                    transitive=self._is_transitive_dependency(
                        pyproject_file_content, name
                    ),
                )
            )

        return dependencies

    def get_runtime_version(self) -> str | None:
        """Return the runtime version according to the pyproject.toml file."""
        return None
