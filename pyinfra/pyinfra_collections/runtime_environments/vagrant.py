"""Vagrant installation."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Vagrant")
def configure_vagrant(user=None, home=None, _sudo=None):
    """Install Vagrant."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_vagrant", False)):
        return

    # Add HashiCorp APT repository (if not already added)
    apt.repo(
        name="Add HashiCorp APT repository",
        src="deb [arch=amd64 signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com jammy main",
    )

    # Update apt cache
    apt.update(
        name="Update apt cache",
    )

    # Install vagrant
    apt.packages(
        name="Install Vagrant",
        packages=["vagrant"],
    )
