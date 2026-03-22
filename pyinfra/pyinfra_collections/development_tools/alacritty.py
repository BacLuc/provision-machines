"""Alacritty terminal emulator setup."""

import os
from io import StringIO

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, files


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Alacritty")
def configure_alacritty(user=None, home=None, font_size=12, _sudo=None, **kwargs):
    """Setup Alacritty terminal emulator with Catppuccin Mocha theme."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_alacritty", False)):
        return

    # Get user/home from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    if home is None:
        home = f"/home/{user}"

    # Get font_size from host.data if not provided
    if font_size == 12:
        font_size = host.data.get("alacritty", {}).get("font_size", 12)

    # Install Alacritty via apt
    apt.packages(
        name="Install Alacritty",
        packages=["alacritty"],
        update=True,
    )

    # Create Alacritty config directory
    files.directory(
        name="Create Alacritty config directory",
        path=f"{home}/.config/alacritty",
        mode="755",
    )

    # Download Catppuccin Mocha theme
    files.download(
        name="Download Catppuccin Mocha theme",
        src="https://raw.githubusercontent.com/catppuccin/alacritty/f6cb5a5c2b404cdaceaff193b9c52317f62c62f7/catppuccin-mocha.toml",
        dest=f"{home}/.config/alacritty/catppuccin-mocha.toml",
        mode="644",
    )

    # Create Alacritty configuration
    config_content = f"""import = [
    "~/.config/alacritty/catppuccin-mocha.toml"
]

[font]
size = {font_size}

[mouse]
hide_when_typing = false

[window]
startup_mode = "Maximized"
"""

    files.put(
        name="Create Alacritty configuration file",
        src=StringIO(config_content),
        dest=f"{home}/.config/alacritty/alacritty.toml",
        mode="644",
    )
