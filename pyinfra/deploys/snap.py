from pyinfra import host
from pyinfra.operations import server

snap_defaults = {
    "refresh": {
        "timer": "4:00-9:00",
    },
}

snap = snap_defaults.copy()
if host.data.get("snap"):
    snap.update(host.data.get("snap", {}))

if host.data.get("snap", {}).get("enabled", False):
    
    server.shell(
        name="Set snap refresh timer",
        commands=[f"sudo snap set system refresh.timer={snap['refresh']['timer']}"],
        _sudo=True,
    )
    
    # Install snaps (would need to be implemented with shell commands)
    snaps = host.data.get("snaps", [])
    if snaps:
        for snap_pkg in snaps:
            server.shell(
                name=f"Install snap {snap_pkg}",
                commands=[f"snap install {snap_pkg}"],
                _sudo=True,
            )
    
    # Install classic snaps
    classic_snaps = host.data.get("classic_snaps", [])
    if classic_snaps:
        for snap_pkg in classic_snaps:
            server.shell(
                name=f"Install classic snap {snap_pkg}",
                commands=[f"snap install {snap_pkg} --classic"],
                _sudo=True,
            )