import json
import os

from github import Github


def get_latest_commit_hash_of_pr() -> str:
    """Get commit hash of the latest commit of the current PR."""
    with open(os.environ["GITHUB_EVENT_PATH"], "r") as f:
        gh_event = json.load(f)

    return gh_event["pull_request"]["head"]["sha"]


def post_github_pr_comment(msg: str) -> None:
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
