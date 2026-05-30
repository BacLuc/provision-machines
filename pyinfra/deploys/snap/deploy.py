from pyinfra import host
from pyinfra.operations import server

snap = {
    "refresh": {
        "timer": "4:00-9:00",
    },
    **host.data.snap,
}

if host.data.snap["enabled"]:
    server.shell(
        name="Set snap refresh timer",
        commands=[f"snap set system refresh.timer={snap['refresh']['timer']}"],
        _sudo=True,
    )
