from pyinfra import host
from pyinfra.operations import apt, files, server


def basicsetup():
    if not host.data.get("basicsetup", {}).get("enabled", False):
        return

    basicsetup_config = host.data.basicsetup

    apt.packages(
        name="Install basic tools",
        packages=basicsetup_config.get("basic_tools", []),
        _sudo=True,
    )

    server.shell(
        name="Set timezone to Europe/Zurich",
        commands=["timedatectl set-timezone Europe/Zurich"],
        _sudo=True,
    )

    server.shell(
        name="Set locale to en_US.UTF-8",
        commands=["locale-gen en_US.UTF-8"],
        _sudo=True,
    )

    files.line(
        name="Set default locale to en_US.UTF-8",
        path="/etc/default/locale",
        line='LC_ALL="en_US.UTF-8"',
        regex="LC_ALL",
        _sudo=True,
    )

    apt.packages(
        name="Install additional packages",
        packages=basicsetup_config.get("additional_tools", []),
        _sudo=True,
    )