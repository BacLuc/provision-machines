from operations.filesystem import DEPLOYS_DIR, dirname_of
from pyinfra import host, local
from pyinfra.operations import (
    apt,
    files,
    flatpak,
    server,
)

if host.data.flatpak["enabled"]:
    apt.packages(
        name="Install flatpak",
        packages=["flatpak"],
        _sudo=True,
    )

    server.shell(
        name="Add flathub repository",
        commands=["flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo"],
        _sudo=True,
    )

    flatpak.packages(
        name="Install flatpaks",
        packages=host.data.flatpaks,
    )

    local.include(f"{DEPLOYS_DIR}/update_packages_script/deploy.py")

    files.put(
        name="Add flatpak update script",
        src=f"{dirname_of(__file__)}/files/flatpak-upgrade.sh",
        dest=f"{host.data.get('update_packages_script', {}).get('dir')}/flatpak-upgrade",
        _sudo=True,
        mode="755",
    )
