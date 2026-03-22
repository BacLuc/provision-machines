"""Deploy script - run pyinfra with different configurations.

Usage:
    poetry run deploy                    # Deploy to local with defaults
    poetry run deploy --limit ci         # Deploy with CI config
    poetry run deploy --limit laptop     # Deploy with laptop config
    poetry run deploy --limit desktop    # Deploy with desktop config
    poetry run deploy --dry              # Dry run (show changes without applying)
    poetry run deploy -y                 # Deploy without confirmation
    poetry run deploy --limit ci -y      # Deploy CI without confirmation
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    """Run pyinfra deploy with specified configuration."""
    parser = argparse.ArgumentParser(description="Deploy with pyinfra")
    parser.add_argument(
        "--limit",
        type=str,
        default="@local",
        help="Limit to specific group or host (default: @local). Options: ci, laptop, desktop, @local",
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        help="Dry run (show changes without applying)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompts",
    )
    parser.add_argument(
        "extra_args",
        nargs="*",
        help="Additional arguments passed to pyinfra",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    # Build pyinfra command
    pyinfra_args = ["inventory.py", "deploy.py", "--limit", args.limit]

    if args.dry:
        pyinfra_args.insert(0, "--dry")

    if args.yes:
        pyinfra_args.insert(0, "--yes")

    # Add any extra arguments
    pyinfra_args.extend(args.extra_args)

    result = subprocess.run(
        ["pyinfra", *pyinfra_args],
        cwd=project_root,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
