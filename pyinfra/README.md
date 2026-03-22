# Provision Machines

Provision development machines using Pyinfra.

## Installation

```bash
poetry install
```

## Usage

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

## Configuration

Configuration is managed via Pyinfra's idiomatic `group_data` system:

### Group Data Files

- `group_data/all.py` - Default configuration (all modules disabled)
- `group_data/ci.py` - CI-specific configuration
- `group_data/laptop.py` - Laptop-specific configuration (gitignored)

There is an example inventory/local.yaml to show what was overridden on one laptop.

## Fetching config

Do not pass config down, it is injected via `poetry.host`
You can access config values via `host.data.get("enable_zsh", False)`.
No parsing of booleans is needed.
