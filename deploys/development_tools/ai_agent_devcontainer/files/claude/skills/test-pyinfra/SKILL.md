---
name: test-pyinfra
description: Test pyinfra deploys, linting, type checking, formatting, and provisioning in the provision-machines repository.
---

# Testing pyinfra in provision-machines

## Repo overview

- `deploys/` — the deploy scripts, one directory per deploy (e.g. `deploys/docker/deploy.py`)
- `operations/` — reusable pyinfra operations (e.g. `operations/filesystem.py`) with tests next to them (e.g. `operations/filesystem_test.py`)
- `inventory.py` — the pyinfra inventory
- `group_data/` — group data (e.g. `group_data/all.py`, `group_data/ci.py`)

## Setup

```bash
uv sync --all-extras
```

## Test suite

```bash
uv run pytest
```

Tests use pytest-cov and are named `*_test.py`, living next to the code they test — e.g. `operations/filesystem_test.py`, NOT `tests/filesystem_test.py`.

## Linting

```bash
uv run ruff check .
```

## Type checking

```bash
uv run mypy .
```

## Formatting

Run prettier in a docker container, then verify nothing changed:

```bash
docker run --rm -v $PWD:/workdir -w /workdir -u $UID ghcr.io/bacluc/prettier-image/prettier-image:5.1.0
git diff --exit-code
```

## Full local provisioning

```bash
uv run scripts/run_pyinfra_local.py
```

This runs the whole `run.py` deploy with `-y`. It requires the `SUDO_PASSWORD` environment variable to be set.

## Second run with only the changed deploy

After a change, re-run only the changed deploy plus its dependents to verify idempotency:

```bash
uv run pyinfra inventory.py deploys/<name>/deploy.py -y
```

NOTE: `scripts/run_pyinfra_single.py` does NOT pass `-y`, so it prompts interactively — use the direct `uv run pyinfra ... -y` form instead.

Find which deploys include a given deploy (dependents) via:

```bash
grep -rn "local.include" deploys/
```

## Verify the result

- Expected resources changed (the ones your deploy touches)
- Unexpected resources did NOT change (nothing else was touched)

## When to use

This skill loads when developing pyinfra things in this repository.