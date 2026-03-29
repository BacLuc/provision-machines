"""HashiCorp Vault CLI installation."""

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


@deploy("HashiCorp Vault CLI")
def configure_hashicorp_vault_cli(user=None, home=None, _sudo=None):
    """Install HashiCorp Vault CLI."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_hashicorp_vault_cli", False)):
        return

    # Add HashiCorp APT repository
    server.shell(
        name="Add HashiCorp APT repository key",
        commands=[
            "wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg"
        ],
        _ignore_errors=True,
    )

    # Get OS release
    server.shell(
        name="Get Ubuntu release codename",
        commands=[". /etc/os-release && echo $VERSION_CODENAME"],
    )

    # Add repository
    apt.repo(
        name="Add HashiCorp APT repository",
        src="deb [arch=amd64 signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com jammy main",
    )

    # Update apt cache
    apt.update(
        name="Update apt cache",
    )

    # Install vault
    apt.packages(
        name="Install Vault",
        packages=["vault"],
    )
