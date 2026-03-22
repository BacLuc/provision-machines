"""Pyinfra inventory file.

Defines groups of hosts for different deployment scenarios.

Usage:
    pyinfra inventory.py deploy.py --limit @local    # Deploy to local machine with defaults
    pyinfra inventory.py deploy.py --limit ci        # Deploy with CI config
    pyinfra inventory.py deploy.py --limit laptop    # Deploy with laptop config
"""

# Local machine (default)
local = ["@local"]

# CI environment
ci = ["@local"]

# Laptop configuration
laptop = ["@local"]

# Desktop configuration
desktop = ["@local"]
