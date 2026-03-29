"""Homebrew installation and configuration."""

import os

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server, files, apt


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Homebrew")
def configure_homebrew(user=None, home=None, _sudo=None):
    """Setup Homebrew for Linux."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_homebrew", False)):
        return

    # Get user/home from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    if home is None:
        home = f"/home/{user}"

    # Create linuxbrew directory structure
    server.shell(
        name="Create linuxbrew directory",
        commands=["mkdir -p /home/linuxbrew/.linuxbrew"],
    )

    # Install homebrew if not already installed
    server.shell(
        name="Install Homebrew",
        commands=[
            "command -v brew || /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        ],
        _ignore_errors=True,
    )

    # Add brew to PATH
    files.line(
        name="Add brew to PATH in .bashrc",
        path=f"{home}/.bashrc",
        line='eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"',
        ensure_newline=True,
    )
