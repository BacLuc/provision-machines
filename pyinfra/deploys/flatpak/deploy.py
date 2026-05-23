from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
    server,
)

# Install flatpak
apt.packages(
    name="Install flatpak",
    packages=["flatpak"],
    _sudo=True,
)

# Add flathub repository
server.shell(
    name="Add flathub repository",
    commands=["flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo"],
    _sudo=True,
)

# Install flatpaks if defined
if host.data.get("flatpaks"):
    # Note: flatpak operations would need to be implemented separately
    # as pyinfra doesn't have direct flatpak support
    pass

# Add update script
if host.data.get("update_packages_script", {}).get("dir"):
    files.put(
        name="Add flatpak update script",
        src="files/flatpak-upgrade.sh",
        dest=f"{host.data.get('update_packages_script', {}).get('dir')}/flatpak-upgrade",
        _sudo=True,
        mode="755",
    )