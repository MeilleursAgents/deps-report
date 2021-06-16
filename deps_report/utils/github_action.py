import json
import os

from github import Github
from tabulate import tabulate

from deps_report.models.results import ErrorResult, VersionResult, VulnerabilityResult


def _get_latest_commit_hash_of_pr() -> str:
    """Get commit hash of the latest commit of the current PR."""
    with open(os.environ["GITHUB_EVENT_PATH"], "r") as f:
        gh_event = json.load(f)

    return gh_event["pull_request"]["head"]["sha"]


def _post_github_pr_comment(msg: str) -> None:
    """Post or update comment on Github PR corresponding to current event."""
    with open(os.environ["GITHUB_EVENT_PATH"], "r") as f:
        gh_event = json.load(f)

    github = Github(os.environ["INPUT_GITHUB_TOKEN"])
    gh_repo = github.get_repo(gh_event["repository"]["full_name"])
    gh_pr = gh_repo.get_pull(gh_event["number"])

    existing_comment = None
    for comment in gh_pr.get_issue_comments():
        if comment.user.type == "Bot" and "deps-report" in comment.body:
            existing_comment = comment
            break

    if existing_comment:
        existing_comment.edit(msg)
    else:
        gh_pr.create_issue_comment(msg)


def send_github_pr_comment_with_results(
    versions_results: list[VersionResult],
    vulnerabilities_results: list[VulnerabilityResult],
    errors_results: list[ErrorResult],
) -> None:
    """Print results as a comment on the current Github PR."""
    if "GITHUB_EVENT_PATH" not in os.environ and "INPUT_GITHUB_TOKEN" not in os.environ:
        return

    msg = ""
    if len(vulnerabilities_results) > 0:
        msg += "## Vulnerable dependencies\n"
        msg += f"<details><summary> <b>{len(vulnerabilities_results)}</b> dependencies have vulnerabilities 😱</summary>\n\n"
        vulnerabilities_table = tabulate(
            [
                (item.dependency_name, item.advisory, item.impacted_versions)
                for item in vulnerabilities_results
            ],
            ["Dependency", "Advisory", "Versions impacted"],
            tablefmt="github",
        )
        msg += f"{vulnerabilities_table}\n</details>\n\n"

    msg += "## Outdated dependencies\n"
    if len(versions_results) > 0:
        msg += f"<details><summary> <b>{len(versions_results)}</b> outdated dependencies found 😢</summary>\n\n"
        versions_table = tabulate(
            [
                (item.dependency_name, item.installed_version, item.latest_version)
                for item in versions_results
            ],
            ["Dependency", "Installed version", "Latest version"],
            tablefmt="github",
        )
        msg += f"{versions_table}\n</details>\n\n"
    else:
        msg += "No outdated dependencies found 🎉\n"

    if msg:
        msg = f"# **deps-report 🔍**\nCommit scanned: {_get_latest_commit_hash_of_pr()[:7]}\n{msg}"
        _post_github_pr_comment(msg)
