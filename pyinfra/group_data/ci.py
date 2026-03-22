# CI-specific configuration overrides
# Applied when deploying with --limit ci

import os

# User configuration
user = os.environ.get("USER", "runner")

# Runtime environments - enable for CI testing
enable_docker = True
enable_python = True

# Development tools - enable for CI testing
enable_nvim = True

# Python configuration for CI
python = {
    "venvs": [
        {
            "name": "test",
            "python_version": "3.11",
        }
    ],
    "pyenv_dir": None,
}

# Debug settings for CI
debug = True
verbose = True
