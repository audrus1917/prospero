# GitHub CLI

GitHub CLI (`gh`) is the official command-line client for GitHub. It can create
pull requests, inspect GitHub Actions runs, manage releases, and call the GitHub
API without opening the web interface.

## Installation

Follow the official instructions for your operating system:

- <https://cli.github.com/>
- <https://github.com/cli/cli/blob/trunk/docs/install_linux.md>

Verify the installation:

```bash
gh --version
```

## Authentication

Sign in interactively:

```bash
gh auth login
```

Choose `GitHub.com`, then either HTTPS or SSH for Git operations. Browser-based
authentication is usually the simplest option. Check the current account with:

```bash
gh auth status
```

Do not put GitHub tokens in the repository, shell history, documentation, or
`.env` files.

## Common commands

Run these commands from the repository directory:

```bash
# Inspect the repository
gh repo view

# Create a pull request for the current branch
gh pr create --fill

# Show pull requests
gh pr list

# Watch CI checks for a pull request
gh pr checks --watch

# Inspect recent GitHub Actions runs
gh run list
gh run view <run-id> --log-failed

# Open the repository or current pull request in a browser
gh repo view --web
gh pr view --web
```

## How Codex uses it

Codex uses `gh` only when the task explicitly requires interaction with GitHub,
for example to create a pull request, inspect CI, publish a release, or configure
repository settings. Before mutating GitHub state, Codex inspects the local Git
state and keeps changes within the repository named in the task.

Authentication belongs to the local user. Codex must not print, commit, or store
credentials in the project. Temporary authentication data should be removed when
the task is complete.
