"""Flatpak installation and configuration."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, server, files


@deploy("Flatpak")
def setup_flatpak(flatpaks=None, _sudo=None):
    """Install and configure Flatpak with Flathub repository."""
    # Install flatpak
    apt.packages(
        name="Install flatpak",
        packages=["flatpak"],
        update=True,
    )

    # Add Flathub repository
    server.shell(
        name="Add Flathub repository",
        commands=["flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo"],
        _ignore_errors=True,
    )

    # Install flatpaks if specified
    if flatpaks:
        for app in flatpaks:
            server.shell(
                name=f"Install {app}",
                commands=[f"flatpak install -y {app}"],
            )
