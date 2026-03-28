"""MOTD (Message of the Day) configuration."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import files, server


@deploy("MOTD")
def configure_motd(enable_disk_usage=True, _sudo=None):
    """Configure Message of the Day (MOTD) settings."""
    # Create disk usage script for MOTD
    if enable_disk_usage:
        files.put(
            name="Create disk usage MOTD script",
            src="/bin/sh\ndf -h | grep -v tmpfs\n",
            dest="/etc/update-motd.d/50-disk-usage",
            mode="755",
        )


@deploy("MOTD")
def setup_motd(enable_disk_usage=False, _sudo=None):
    """Setup MOTD configuration."""
    if enable_disk_usage:
        configure_motd()
