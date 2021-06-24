import json
import os
from typing import Any

import toml

from deps_report.models import Dependency, DependencyRepository
from deps_report.utils.templating import expand_template_string_with_env


class PythonPipenvParser:

    DEFAULT_REPOSITORY = DependencyRepository(
        name="pypi",
        url="https://pypi.org/simple",
    )

    def _get_file_paths(self, given_file_path: str) -> tuple[str, str]:
        """Get a tuple containing the file path for Pipfile and the file path for Pipfile.lock."""
        given_path, given_filename = os.path.split(given_file_path)

        if given_filename == "Pipfile.lock":
            return os.path.join(given_path, "Pipfile"), given_file_path
        elif given_filename == "Pipfile":
            return (
                given_file_path,
                os.path.join(given_path, "Pipfile.lock"),
            )

        raise ValueError(
            "Invalid file path provided: you need to specify the path to your Pipfile or Pipfile.lock file"
        )

    def __init__(self, given_file_path: str) -> None:
        """Create the parser for the given Pipfile/Pipfile.lock file path."""
        self.pipenv_file_path, self.pipenv_lock_file_path = self._get_file_paths(
            given_file_path
        )

    def _get_repositories(self) -> dict[str, DependencyRepository]:
        with open(self.pipenv_lock_file_path, "r") as lock_file:
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
        if explicit_repo and explicit_repo in all_repositories:
            return [all_repositories[explicit_repo]] + [
                item for item in all_repositories.values() if item.name != explicit_repo
            ]

        return [self.DEFAULT_REPOSITORY] + [
            item
            for item in all_repositories.values()
            if item.url != self.DEFAULT_REPOSITORY.url
        ]

    def _is_transitive_dependency(
        self, pipenv_file_content: Any, dependency_name: str
    ) -> bool:
        """Check if a dependency is transitive by looking if it's present in the Pipfile."""
        return (
            dependency_name not in pipenv_file_content["dev-packages"]
            and dependency_name not in pipenv_file_content["packages"]
        )

    def _get_dependencies_from_lockfile_section(
        self,
        pipenv_file_content: Any,
        lock_file_content: Any,
        section_name: str,
        repositories: dict[str, DependencyRepository],
    ) -> list[Dependency]:
        parsed_dependencies = []

        for dependency_name, dependency_dict in lock_file_content[section_name].items():
            parsed_dependencies.append(
                Dependency(
                    name=dependency_name,
                    version=dependency_dict["version"].replace("==", ""),
                    repositories=self._get_repositories_for_dependency(
                        repositories, dependency_dict
                    ),
                    transitive=self._is_transitive_dependency(
                        pipenv_file_content, dependency_name
                    ),
                    for_dev=True if section_name == "develop" else False,
                )
            )

        return parsed_dependencies

    def get_dependencies(self) -> list[Dependency]:
        """Parse the Pipfile.lock file to return a list of the dependencies."""
        with open(self.pipenv_lock_file_path, "r") as lock_file:
            lock_file_content = json.load(lock_file)

        with open(self.pipenv_file_path, "r") as pipenv_file:
            pipenv_file_content = toml.load(pipenv_file)

        repositories = self._get_repositories()
        parsed_dependencies = self._get_dependencies_from_lockfile_section(
            pipenv_file_content, lock_file_content, "default", repositories
        )

        # add dev dependencies if not already present
        dev_dependencies = self._get_dependencies_from_lockfile_section(
            pipenv_file_content, lock_file_content, "develop", repositories
        )

        for dependency in dev_dependencies:
            if any(item.name == dependency.name for item in parsed_dependencies):
                continue
            parsed_dependencies.append(dependency)

        parsed_dependencies.sort(key=lambda x: x.name)
        return parsed_dependencies
