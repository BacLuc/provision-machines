from pyinfra import host
from pyinfra.operations import server, snap

if host.data.snap["enabled"]:
    server.shell(
        name="Set snap refresh timer",
        commands=[f"snap set system refresh.timer={host.data.snap['refresh']['timer']}"],
        _sudo=True,
    )

    if host.data.snaps:
        snap.package(
            name="Install snaps",
            packages=host.data.snaps,
            _sudo=True,
        )

    if host.data.classic_snaps:
        snap.package(
            name="Install classic snaps",
            packages=host.data.classic_snaps,
            classic=True,
            _sudo=True,
        )
