from pyinfra import host, local
from pyinfra.facts.server import Command
from pyinfra.operations import (
    apt,
    files,
    flatpak,
    server,
)

from operations.filesystem import DEPLOYS_DIR, dirname_of

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

    server.shell(
        name="Set Flatpak cursor theme",
        commands=["flatpak override --user --env=XCURSOR_THEME=Adwaita"],
    )

    local.include(f"{DEPLOYS_DIR}/update_packages_script/deploy.py")

    files.put(
        name="Add flatpak update script",
        src=f"{dirname_of(__file__)}/files/flatpak-upgrade.sh",
        dest=f"{host.data.get('update_packages_script', {}).get('dir')}/flatpak-upgrade",
        _sudo=True,
        mode="755",
    )
else:
    flatpak_cli = host.get_fact(Command, "command -v flatpak || true")
    server.shell(
        name="Remove Flatpak cursor theme override",
        commands=["flatpak override --user --unset-env=XCURSOR_THEME"],
        _if=lambda: bool(flatpak_cli),
    )
