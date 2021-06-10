# deps-report

Display a report of the outdated dependencies for a specified lockfile.
It can be run locally or as Github Action.
If run as a Github action on PRs, it will comment on the PR to display the results.

## Supported dependencies formats
- Pipenv (through the `Pipfile.lock` file)

## Usage

### Locally

Run the tool with the file specified as a path:
`deps-report Pipfile.lock`

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
```
