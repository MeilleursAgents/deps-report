import json
import os
from typing import Any

from deps_report.models import Dependency, DependencyRepository
from deps_report.utils.templating import expand_template_string_with_env


class PythonPipenvParser:

    DEFAULT_REPOSITORY = DependencyRepository(
        name="pypi",
        url="https://pypi.org/simple",
    )

    def _get_lock_path(self, given_file_path: str) -> str:
        path, filename = os.path.split(given_file_path)

        if filename == "Pipfile.lock":
            return given_file_path

        filename = os.path.splitext(filename)[0]
        new_filename = "ok_%s.txt" % filename
        new_path = os.path.join(path, new_filename)

        return new_path

    def __init__(self, file_path: str) -> None:
        """Create the parser for the specified Pipfile/Pipfile.lock file."""
        self.file_path = self._get_lock_path(file_path)

    def _get_repositories(self) -> dict[str, DependencyRepository]:
        with open(self.file_path, "r") as lock_file:
            file_content = json.load(lock_file)

        parsed_repositories = {}
        for repository in file_content["_meta"]["sources"]:
            name = repository["name"]
            parsed_repositories[name] = DependencyRepository(
                name=name,
                url=expand_template_string_with_env(repository["url"]),
            )

        if self.DEFAULT_REPOSITORY.name not in parsed_repositories:
            parsed_repositories[self.DEFAULT_REPOSITORY.name] = self.DEFAULT_REPOSITORY

        return parsed_repositories

    def _get_repositories_for_dependency(
        self,
        all_repositories: dict[str, DependencyRepository],
        dependency_dict: dict[str, Any],
    ) -> list[DependencyRepository]:
        # Check if repository specified in lockfile
        # if it's the case return list with this repo first,
        # but still include other as sometimes the explicit repository
        # is the wrong one
        explicit_repo = dependency_dict.get("index")
        if explicit_repo:
            return [all_repositories[explicit_repo]] + [
                item for item in all_repositories.values() if item.name != explicit_repo
            ]

        return [self.DEFAULT_REPOSITORY] + [
            item
            for item in all_repositories.values()
            if item.url != self.DEFAULT_REPOSITORY.url
        ]

    def get_dependencies(self) -> list[Dependency]:
        """Parse the Pipfile.lock file to return a list of the dependencies."""
        with open(self.file_path, "r") as lock_file:
            file_content = json.load(lock_file)

        repositories = self._get_repositories()
        parsed_dependencies = []
        for dependency_name, dependency_dict in file_content["default"].items():

            parsed_dependencies.append(
                Dependency(
                    name=dependency_name,
                    version=dependency_dict["version"].replace("==", ""),
                    repositories=self._get_repositories_for_dependency(
                        repositories, dependency_dict
                    ),
                )
            )

        return parsed_dependencies
