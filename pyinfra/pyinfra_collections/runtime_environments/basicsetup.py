"""Basic system setup - timezone, locale, and essential packages."""

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


@deploy("Basic Setup")
def configure_basicsetup(user=None, home=None, _sudo=None):
    """Configure basic system settings."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_basicsetup", True)):
        return

    # Install basic tools
    basic_tools = host.data.get("basic_tools", [
        "curl",
        "wget",
        "git",
        "vim",
        "htop",
        "tree",
        "jq",
        "unzip",
    ])

    apt.packages(
        name="Install basic tools",
        packages=basic_tools,
        update=True,
    )

    # Set timezone
    timezone = host.data.get("timezone", "Europe/Zurich")
    server.shell(
        name="Set timezone to Europe/Zurich",
        commands=[f"timedatectl set-timezone {timezone}"],
        _ignore_errors=True,
    )

    # Generate locale
    server.shell(
        name="Set locale to en_US.UTF-8",
        commands=["locale-gen en_US.UTF-8"],
        _ignore_errors=True,
    )

    # Set default locale
    server.shell(
        name="Set default locale to en_US.UTF-8",
        commands=['echo "LC_ALL=en_US.UTF-8" >> /etc/environment'],
        _ignore_errors=True,
    )

    # Install additional tools
    additional_tools = host.data.get("additional_tools", [
        "software-properties-common",
        "build-essential",
    ])

    apt.packages(
        name="Install additional packages",
        packages=additional_tools,
    )
