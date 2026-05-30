import io

from pyinfra import host
from pyinfra.operations import files, server

if host.data.sysctl["enabled"]:
    settings = host.data.sysctl["settings"]

    files.directory(
        name="Create sysctl.d directory",
        path="/etc/sysctl.d",
        _sudo=True,
        mode="755",
    )

    content = "\n".join(f"{key} = {value}" for key, value in settings.items()) + "\n"

    sysctl_file = files.put(
        name="Create 99-local.conf with sysctl settings",
        src=io.StringIO(content),
        dest="/etc/sysctl.d/99-local.conf",
        _sudo=True,
        mode="644",
    )

    server.shell(
        name="Apply sysctl settings immediately",
        commands=["sysctl --system"],
        _sudo=True,
        _if=lambda: sysctl_file.changed,
    )
