# deps-report

Display a report of the outdated dependencies for a specified project.
It can be run locally or as Github Action.
If run as a Github action on PRs, it will comment on the PR to display the results.

## Supported dependencies formats

### Pipenv

Use the path to your `Pipfile.lock` or `Pipfile`. Please note that both files need to be present side-by-side, but it should always be the case in a valid pipenv project.

The tool supports fetching dependencies from all repositories implementing [PEP 503 (Simple Repository API)](https://www.python.org/dev/peps/pep-0503/) and has been tested with pypi and [packagecloud](https://packagecloud.io/).

If your repository URL contains a templated URL (for example a token for a private repository), it will be automatically expanded if the variable is set in the environment:
```
...
[[source]]
name = "ma"
url = "https://${MY_REPO_TOKEN}:@packagecloud.io/my_org/my_repo/pypi/simple"
verify_ssl = true
...
```

### Poetry

Use the path to your `poetry.lock` or `pyproject.toml` file. Please note that both files need to be present side-by-side, but it should always be the case in a valid poetry project.

⚠️ The Poetry format only support PyPI dependencies for now. Other sources are not supported.

## Usage

deps-report doesn't need to be in the app environment. It works by parsing the lockfiles only.

### Locally

The tool has been tested on Python 3.9. If it is not available on your OS you can use [pyenv](https://github.com/pyenv/pyenv).

You need to install [poetry](https://python-poetry.org/) to install the projects dependency with `poetry install`.

Then you can run the tool with the file specified as a path:
`poetry run deps-report Pipfile.lock`.

### As a Github Action

To run as a Github action, you can use the following snippet.
You just need to adjust the `file` parameter to indicate the path to your lockfile.
The `GITHUB_TOKEN` secret (provided automatically by Github) is needed to comment on the PR.
```yaml
---
name: Dependencies report
on: [pull_request]
jobs:
  build:
    name:  Dependencies report
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v2
      - name: deps-report
        uses: MeilleursAgents/deps-report@master
        with:
          file: Pipfile.lock
          github_token: ${{ secrets.GITHUB_TOKEN }}
        #env:
        #  MY_REPO_TOKEN: ${{ secrets.MY_REPO_TOKEN }}  # if you need a token for a private repository
```

Using a monorepo with multiple apps? You can use the `paths` filter option of Github Actions to limit to your current app:
```yaml
---
name: Dependencies report
on:
  pull_request:
    paths:
      - 'apps/MY_APP/*'
jobs:
  build:
    name:  Dependencies report
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v2
      - name: deps-report
        uses: MeilleursAgents/deps-report@master
        with:
          file: apps/MY_APP/Pipfile.lock
          github_token: ${{ secrets.GITHUB_TOKEN }}
        #env:
        #  MY_REPO_TOKEN: ${{ secrets.MY_REPO_TOKEN }}  # if you need a token for a private repository
```
