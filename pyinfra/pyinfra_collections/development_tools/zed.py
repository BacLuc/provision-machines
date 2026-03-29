"""Zed editor installation and configuration."""

import os
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


@deploy("Zed")
def configure_zed(user=None, home=None, _sudo=None):
    """Install and configure Zed editor."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_zed", False)):
        return

    home = home or os.path.expanduser("~")
    bin_dir = os.path.join(home, "bin")
    local_bin = os.path.join(home, ".local", "bin")

    # Ensure ~/bin exists
    files.directory(
        name="Create ~/bin directory",
        path=bin_dir,
        present=True,
        mode="755",
    )

    # Install zed
    server.shell(
        name="Install Zed editor",
        commands=["curl -f https://raw.githubusercontent.com/zed-industries/zed/refs/tags/v0.204.5/script/install.sh | sh"],
        _ignore_errors=True,
    )

    # Create symlink if zed is installed
    server.shell(
        name="Create zed symlink in ~/bin",
        commands=[f"ln -sf {local_bin}/zed {bin_dir}/zed"],
        _ignore_errors=True,
    )

    # Remove flatpak version if present
    server.shell(
        name="Remove flatpak zed if present",
        commands=["flatpak remove -y dev.zed.Zed || true"],
        _ignore_errors=True,
    )
