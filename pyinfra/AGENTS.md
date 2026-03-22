# Development Machine Provisioning

This pyinfra project provisions development laptops.

## Development Setup

**Prerequisites:** Python 3.8+, Poetry

**Setup commands:**
```bash
pip install poetry
poetry install
poetry shell
```

## Development Workflow


### Deployment

```bash
poetry run deploy                    # Deploy to local with defaults
poetry run deploy --limit ci         # Deploy with CI config
poetry run deploy --dry              # Dry run (show changes without applying)
```

### Linting and Formatting

```bash
poetry run ruff-cmd check          # Check linting
poetry run ruff-cmd check --fix    # Fix linting issues
poetry run ruff-cmd format         # Format code
```

### Testing

```bash
poetry run pytest
```

**Testing guidelines:**
- Don't make token tests that just check attribute existence
- Use virtual filesystem to test file creation
- Keep tests simple - assert minimal changes per collection
- Don't include parse_pool tests (test in one place only)
- Assume pyinfra is available in all environments

Always run the files you changed and check if they do the correct thing.

## Renovate Configuration

Renovate updates all dependencies via regex patterns:

**JSON config:**
```json
{
  "customType": "regex",
  "managerFilePatterns": ["/^.*.ya?ml/"],
  "matchStrings": [
    "renovate: datasource=(?<datasource>.*?) depName=(?<depName>.*?)?\\s.*tag: \"(?<currentValue>.*)\"\\s"
  ]
}
```

**YAML usage:**
```yaml
# renovate: datasource=docker depName=node
tag: "24.13.0"

ollama_defaults:
  # renovate: datasource=github-releases depName=ollama/ollama
  ollama_version: "0.15.2"
```

**Maintenance:** Run `./scripts/update-renovate-snapshot.sh` to verify dependency extraction and update snapshots.

## Python Guidelines

- Module inclusion logic should be in the module itself
- Keep tests minimal and focused
- No pyinfra availability fallback code needed

## Configuration Access

- Config is injected via `poetry.host` 
- Access values with `host.data.get("enable_zsh", False)`
- No boolean parsing required

## Previous Implementation

Reference: Download https://github.com/BacLuc/provision-machines/tree/devel to /tmp/provision-machines
