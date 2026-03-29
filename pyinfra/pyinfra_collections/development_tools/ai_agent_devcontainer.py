"""AI Agent DevContainer setup."""

import os
from io import StringIO

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server, files


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("AI Agent DevContainer")
def configure_ai_agent_devcontainer(user=None, home=None, _sudo=None):
    """Configure AI Agent DevContainer."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_ai_agent_devcontainer", False)):
        return

    # Get user from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    home = home or f"/home/{user}"
    bin_dir = os.path.join(home, "bin")

    # Ensure user bin directory exists
    files.directory(
        name="Create user bin directory",
        path=bin_dir,
        present=True,
        mode="755",
    )

    # Create start-ai-agent-devcontainer script
    script_content = """#!/bin/bash
# Start AI Agent DevContainer

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if .devcontainer.json exists
if [ ! -f "$PROJECT_ROOT/.devcontainer/devcontainer.json" ]; then
    echo "Error: .devcontainer/devcontainer.json not found"
    exit 1
fi

# Run devcontainer up
devcontainer up --workspace-folder "$PROJECT_ROOT"

# Attach to the container
devcontainer exec --workspace-folder "$PROJECT_ROOT" /bin/bash
"""

    files.put(
        name="Create start-ai-agent-devcontainer script",
        src=StringIO(script_content),
        dest=f"{bin_dir}/start-ai-agent-devcontainer",
        mode="755",
    )
