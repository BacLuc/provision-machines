"""Ruff script - run ruff linting and formatting.

Usage:
    poetry run ruff-cmd check          # Check linting
    poetry run ruff-cmd check --fix    # Fix linting issues
    poetry run ruff-cmd format         # Format code
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run ruff with the provided arguments."""
    project_root = Path(__file__).parent.parent

    # Pass all arguments to ruff
    args = sys.argv[1:] if len(sys.argv) > 1 else ["check"]

    result = subprocess.run(
        ["ruff", *args],
        cwd=project_root,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
