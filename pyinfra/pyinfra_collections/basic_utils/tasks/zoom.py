"""Zoom setup."""

from pyinfra.operations import server


def setup():
    """Setup Zoom flatpak."""
    server.shell(
        name="Install Zoom flatpak",
        commands=["flatpak install -y flathub us.zoom.Zoom"],
    )
