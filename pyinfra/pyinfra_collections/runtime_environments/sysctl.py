"""Sysctl configuration."""

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


@deploy("Sysctl")
def configure_sysctl(user=None, home=None, _sudo=None):
    """Configure sysctl settings."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_sysctl", False)):
        return

    # Get sysctl settings with defaults
    sysctl_settings = host.data.get("sysctl_settings", {
        "fs.inotify.max_queued_events": 1048576,
        "fs.inotify.max_user_instances": 1048576,
        "fs.inotify.max_user_watches": 1048576,
    })

    # Create sysctl.d directory
    files.directory(
        name="Create sysctl.d directory",
        path="/etc/sysctl.d",
        present=True,
    )

    # Create sysctl config file using StringIO
    config_content = "# Ansible managed - Local sysctl settings\n"
    for key, value in sysctl_settings.items():
        config_content += f"{key} = {value}\n"

    files.put(
        name="Create 99-local.conf with sysctl settings",
        src=StringIO(config_content),
        dest="/etc/sysctl.d/99-local.conf",
        mode="644",
    )

    # Apply sysctl settings
    server.shell(
        name="Apply sysctl settings immediately",
        commands=["sysctl --system"],
        _ignore_errors=True,
    )
