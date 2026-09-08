---
name: test-github-actions
description: Trigger, monitor, and debug GitHub Actions workflow runs from the command line
---

# Testing GitHub Actions workflows

## Replicate each job step locally

Before triggering a workflow run, read the workflow YAML and run each step's commands locally. This catches most failures faster than a CI round-trip:

```bash
cat .github/workflows/<workflow>.yml
```

Run the commands from each `run:` block in your shell, in order, with the same environment (e.g. `uv sync --frozen`, `uv run pytest`). If a step uses an action (e.g. `actions/checkout`), replicate what it does manually.

## Trigger a workflow run

Three ways, in increasing order of control:

```bash
# 1. push a branch (triggers on: push)
git push origin <branch>

# 2. open a PR (triggers on: pull_request)
gh pr create --base main --head <branch>

# 3. dispatch manually, with inputs
gh workflow run <file> --ref <branch> [--field input=value]
```

For example, to dispatch the verify-renovate workflow with the snapshot update input:

```bash
gh workflow run verify-renovate.yml --ref main --field update_snapshot=true
```

## Inspect results

```bash
# list recent runs
gh run list

# show a run's jobs and status
gh run view <id>

# full log output
gh run view <id> --log

# watch a run until it finishes
gh run watch <id>
```

## Run multiple times with different parameters

After changing a workflow, run it multiple times with different parameters to cover the branches of the logic (e.g. `update_snapshot=true` and `update_snapshot=false` for verify-renovate). A single green run does not prove the workflow handles all inputs.

## Workflows in this repository

- `ci.yaml` — jobs: `pyinfra_lint` (pytest, ruff, mypy, prettier) and `run_pyinfra` (runs pyinfra locally, then update-script and cleanup-script, then pyinfra a second time)
- `verify-renovate.yml` — input: `update_snapshot` boolean; checks dependencies against the renovate snapshot, or updates the snapshot when the input is set

## When to use

This skill loads when developing or modifying GitHub Actions workflows in this repository.