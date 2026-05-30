from pyinfra import host
from pyinfra.operations import flatpak

if host.data.gnome["enable_customize_gnome"]:
    flatpak.packages(
        name="Install gnome extensions app",
        packages=["org.gnome.Extensions"],
    )
