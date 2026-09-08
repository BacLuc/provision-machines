---
name: test-pyinfra
description: Test pyinfra deploys, linting, type checking, formatting, and provisioning in the provision-machines repository.
---

# Testing pyinfra

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
- Verify the resulting files exist (or are removed) and have the expected content
- Verify the services or tools are available, running if possible or can be started. If a tool was installed, verify it works as expected.

Note the tests you performed and their results as response or in the Issue or PR you are working on.

## When to use

This skill loads when developing pyinfra things.
