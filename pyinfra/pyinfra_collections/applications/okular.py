"""Okular PDF viewer installation."""

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


@deploy("Okular")
def configure_okular(user=None, home=None, _sudo=None):
    """Install Okular PDF viewer."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_okular", False)):
        return

    # Install okular
    apt.packages(
        name="Install Okular",
        packages=["okular"],
    )

    # Create gnome defaults file
    files.file(
        name="Create gnome defaults file",
        path="/etc/gnome/defaults.list",
        present=True,
    )

    # Set okular as default PDF viewer
    files.line(
        name="Set okular as default pdf viewer",
        path="/etc/gnome/defaults.list",
        line="application/pdf=okular.desktop",
        ensure_newline=True,
    )
