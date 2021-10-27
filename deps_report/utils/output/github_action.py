import json
import os

from github import Github
from tabulate import tabulate

from deps_report.models import RuntimeInformations
from deps_report.models.results import ErrorResult, VersionResult, VulnerabilityResult
from deps_report.utils.output.common import (
    get_display_output_for_dependency,
    get_number_of_dependencies_with_outdated_major,
)


def _get_workflow_run_url() -> str:
    return f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"


def _is_running_as_github_action() -> bool:
    return "GITHUB_EVENT_PATH" in os.environ and (
        "INPUT_GITHUB_TOKEN" in os.environ or "GITHUB_TOKEN" in os.environ
    )


def _get_github_token() -> str:
    token_as_input = os.environ.get("INPUT_GITHUB_TOKEN")
    if token_as_input:
        return token_as_input

    token_as_env = os.environ.get("GITHUB_TOKEN")
    if token_as_env:
        return token_as_env

    raise ValueError("Doesn't have Github token")


def _get_latest_commit_hash_of_pr() -> str:
    """Get commit hash of the latest commit of the current PR."""
    with open(os.environ["GITHUB_EVENT_PATH"], "r") as f:
        gh_event = json.load(f)

    return gh_event["pull_request"]["head"]["sha"]


def _post_github_pr_comment(msg: str) -> None:
    """Post or update comment on Github PR corresponding to current event."""
    with open(os.environ["GITHUB_EVENT_PATH"], "r") as f:
        gh_event = json.load(f)

    github = Github(_get_github_token())
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
    runtime_informations: RuntimeInformations | None,
) -> None:
    """Print results as a comment on the current Github PR."""
    if not _is_running_as_github_action():
        return

    msg = ""

    if runtime_informations and runtime_informations.current_version_is_outdated:
        msg += f"ℹ️ {runtime_informations.name} version {runtime_informations.current_version} is used by your project but the latest version is {runtime_informations.latest_version}.\n\n"
        if runtime_informations.current_version_is_eol_soon:
            msg += f"🚨<b>Your {runtime_informations.name} version reaches EOL date on {runtime_informations.current_version_eol_date}, you should upgrade !</b>\n\n"

    if len(vulnerabilities_results) > 0:
        msg += "## Vulnerable dependencies\n"
        msg += f"<details><summary> <b>{len(vulnerabilities_results)}</b> dependencies have vulnerabilities 😱</summary>\n\n"
        vulnerabilities_table = tabulate(
            [
                (
                    get_display_output_for_dependency(item.dependency),
                    item.advisory,
                    item.impacted_versions,
                )
                for item in vulnerabilities_results
            ],
            ["Dependency", "Advisory", "Versions impacted"],
            tablefmt="github",
        )
        msg += f"{vulnerabilities_table}\n</details>\n\n"

    msg += "## Outdated dependencies\n"
    if len(versions_results) > 0:
        outdated_major_count = get_number_of_dependencies_with_outdated_major(
            versions_results
        )
        msg += f"<details><summary> <b>{len(versions_results)}</b> outdated dependencies found (including {outdated_major_count} outdated major versions)😢</summary>\n\n"
        versions_table = tabulate(
            [
                (
                    get_display_output_for_dependency(item.dependency),
                    item.installed_version,
                    item.latest_version,
                )
                for item in versions_results
            ],
            ["Dependency", "Installed version", "Latest version"],
            tablefmt="github",
        )
        msg += f"{versions_table}\n</details>\n\n"
    else:
        msg += "No outdated dependencies found 🎉\n\n"

    footer = f"<sub>[*Logs*]({_get_workflow_run_url()})</sub>"
    if msg:
        msg = f"# **deps-report 🔍**\nCommit scanned: {_get_latest_commit_hash_of_pr()[:7]}\n{msg}\n\n{footer}"
        _post_github_pr_comment(msg)
