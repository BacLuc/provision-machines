"""Snap package management."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server


@deploy("Snap")
def configure_snap(snaps=None, refresh_timer="4:00-9:00", _sudo=None):
    """Configure snap packages."""
    # Set refresh timer
    server.shell(
        name="Set snap refresh timer",
        commands=[f"sudo snap set system refresh.timer={refresh_timer}"],
    )

    # Install snaps if provided
    if snaps:
        for snap in snaps:
            server.shell(
                name=f"Install {snap}",
                commands=[f"snap install {snap}"],
            )
