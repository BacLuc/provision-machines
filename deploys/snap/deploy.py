from pyinfra import host, local
from pyinfra.operations import files, server, snap

from operations.filesystem import DEPLOYS_DIR, dirname_of

if host.data.snap["enabled"]:
    server.shell(
        name="Set snap refresh timer",
        commands=[f"snap set system refresh.timer={host.data.snap['refresh']['timer']}"],
        _sudo=True,
    )

    local.include(f"{DEPLOYS_DIR}/cleanup_scripts/deploy.py")

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

    files.put(
        name="Add snap cleanup script",
        src=f"{dirname_of(__file__)}/files/snap-cleanup.sh",
        dest=f"{host.data.cleanup_scripts['dir']}/snap-cleanup",
        _sudo=True,
        mode="755",
    )
