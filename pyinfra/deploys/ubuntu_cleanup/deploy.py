from pyinfra import host
from pyinfra.operations import server

if host.data.ubuntu_cleanup["enabled"]:
    server.shell(
        name="Remove no more referenced packages",
        commands=["apt-get autoremove -y"],
        _sudo=True,
    )
