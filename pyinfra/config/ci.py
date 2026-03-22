# CI-specific configuration overrides
# Applied when CI environment variables are detected
# Higher priority than global config

import os

# Detect CI environment
CI_MODE = (
    os.environ.get("GITHUB_ACTIONS") == "true"
    or os.environ.get("CI") == "true"
    or os.environ.get("JENKINS_URL") is not None
)

if CI_MODE:
    # Override user for CI
    USER = "runner"
    USER_GROUPS = ["sudo", "users"]

    # Enable testing tools in CI
    DOCKER_ENABLE = True
    BASIC_UTILS_ENABLE_SSH_CONFIG = True
    SSH_CONFIG_PATHS = ["/tmp/config.d/*"]

    # Enable Python for testing
    BASIC_UTILS_ENABLE_PYTHON = True
    BASIC_UTILS_PYTHON_VENVS = [
        {
            "name": "test",
            "python_version": "3.11",
            "packages": ["pytest", "pytest-cov", "black", "ruff", "mypy"],
        }
    ]

    # Enable essential dev tools in CI
    DEV_TOOLS_ENABLE_NEOVIM = True

    # CI-specific settings
    DEBUG = True
    VERBOSE = True
    DRY_RUN = False
