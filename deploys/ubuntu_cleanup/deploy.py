from pyinfra import host
from pyinfra.operations import server

if host.data.ubuntu_cleanup["enabled"]:
    server.shell(
        name="Remove no more referenced packages",
        commands=["apt-get -y autoremove"],
        _sudo=True,
    )
