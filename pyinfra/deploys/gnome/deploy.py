from pyinfra import host
from pyinfra.operations import server

if host.data.get("gnome", {}).get("enable_customize_gnome", False):
    # Install gnome extensions app
    # Note: flatpak operations would need to be implemented separately
    # as pyinfra doesn't have direct flatpak support
    server.shell(
        name="Install gnome extensions app",
        commands=["echo 'Would install org.gnome.Extensions via flatpak'"],
    )