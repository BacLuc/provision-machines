"""DisplayLink driver installation."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, server


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("DisplayLink Driver")
def configure_displaylink_driver(user=None, home=None, _sudo=None):
    """Install DisplayLink driver for docking stations."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_displaylink_driver", False)):
        return

    # Check if DisplayLink driver is already installed
    server.shell(
        name="Check if DisplayLink driver is installed",
        commands=["dpkg -l | grep displaylink-driver"],
    )

    # Download Synaptics repository keyring
    server.shell(
        name="Download Synaptics repository keyring",
        commands=[
            "curl -fsSL https://www.synaptics.com/sites/default/files/Ubuntu/pool/stable/main/all/synaptics-repository-keyring.deb -o /tmp/synaptics-repository-keyring.deb"
        ],
        _ignore_errors=True,
    )

    # Install the keyring
    apt.deb(
        name="Install Synaptics repository keyring",
        src="/tmp/synaptics-repository-keyring.deb",
    )

    # Update apt cache
    apt.update(
        name="Update APT cache",
    )

    # Install DisplayLink driver
    apt.packages(
        name="Install DisplayLink driver",
        packages=["displaylink-driver"],
    )
