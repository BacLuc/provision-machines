"""Lazygit installation and configuration."""

import os

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server


@deploy("Lazygit")
def configure_lazygit(user=None, home=None, _sudo=None, **kwargs):
    """Install lazygit via homebrew."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_lazygit", False)):
        return

    # Install lazygit via homebrew
    server.shell(
        name="Install lazygit via homebrew",
        commands=["~/bin/brew install lazygit"],
        _ignore_errors=True,
    )


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)
