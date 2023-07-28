import logging
import os
import pickle
from csv import DictWriter
from logging import DEBUG
from pathlib import Path

from dotenv import load_dotenv
from github import Github, UnknownObjectException
from github.Repository import Repository


load_dotenv()

logger = logging.getLogger()

PATH_PICKLED_REPOS = "ma-repos.pickle"

if __name__ == "__main__":
    logging.basicConfig(level=DEBUG)
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    g = Github(token)

    orga = g.get_organization("MeilleursAgents")
    repos = [repo for repo in orga.get_repos()]
    with Path(PATH_PICKLED_REPOS).open("wb") as path:
        pickle.dump(repos, path)

    # with Path(PATH_PICKLED_REPOS).open("rb") as path:
    #     repos = pickle.load(path)

    MEILLEURS_AGENTS_APPS = {
        "passerelles": "tools/passerelles/",
        "ftp_auth": "tools/passerelle/",
        "filewatch": "tools/filewatch/",
        "SalesforceAPI": "apps/SalesforceAPI/",
    }


    class MeilleursAgentsRepo:
        def __init__(self, github, app, path):
            self._github: Github = github
            self.app = app
            self.path = path
            self.full_name = f"MeilleursAgents/{self.app}"
            self.html_url = f"https://github.com/MeilleursAgents/MeilleursAgents/tree/master/{self.app}"
            self.git_url = "git://github.com/MeilleursAgents/MeilleursAgents.git"

        def get_contents(self, filename):
            full_path = f"{self.path}{filename}"
            return self._github.get_repo(
                "MeilleursAgents/MeilleursAgents").get_contents(full_path)


    meilleurs_agents_repos = [MeilleursAgentsRepo(g, k, v) for k, v in
                              MEILLEURS_AGENTS_APPS.items()]

    repos_dict = []
    all_repos = repos.extend(meilleurs_agents_repos)
    for repo in repos:
        pipfile_content = None
        pipfile_path = None
        pipfile_lock_content = None
        pipfile_lock_path = None
        try:
            pipfile_content = repo.get_contents("Pipfile")
        except UnknownObjectException:
            logger.info("%s : Pipfile.lock not found", repo.full_name)
        else:
            logger.info("%s : Pipfile.lock found", repo.full_name)
            pipfile_path = Path(f"ma-apps/{repo.full_name.lower()}/Pipfile")
            pipfile_path.parent.mkdir(parents=True, exist_ok=True)
            pipfile_path.write_text(pipfile_content.decoded_content.decode("utf-8"))

        try:
            pipfile_lock_content = repo.get_contents("Pipfile.lock")
        except UnknownObjectException:
            logger.info("%s : Pipfile.lock not found", repo.full_name)
        else:
            logger.info("%s : Pipfile.lock found", repo.full_name)
            pipfile_lock_path = Path(f"ma-apps/{repo.full_name.lower()}/Pipfile.lock")
            pipfile_lock_path.parent.mkdir(parents=True, exist_ok=True)
            pipfile_lock_path.write_text(
                pipfile_lock_content.decoded_content.decode("utf-8")
            )

        repos_dict.append(
            {
                "full_name": repo.full_name,
                "html_url": repo.html_url,
                "git_url": repo.git_url,
                "pipfile": str(pipfile_path) if pipfile_content else None,
                "pipfile.lock": str(pipfile_lock_path)
                if pipfile_lock_content
                else None,
            }
        )

    with Path("ma-repos.csv").open("w") as csv_path:
        csv_writer = DictWriter(
            csv_path, ["full_name", "html_url", "git_url", "pipfile", "pipfile.lock"]
        )
        csv_writer.writeheader()
        for i in repos_dict:
            csv_writer.writerow(i)

    logger.info("done")
