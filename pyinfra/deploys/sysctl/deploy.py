import io

from pyinfra import host
from pyinfra.operations import files, server

sysctl = {
    "settings": {
        "fs.inotify.max_queued_events": 1048576,
        "fs.inotify.max_user_instances": 1048576,
        "fs.inotify.max_user_watches": 1048576,
    },
    **host.data.sysctl,
}

if host.data.sysctl["enabled"]:
    files.directory(
        name="Create sysctl.d directory",
        path="/etc/sysctl.d",
        _sudo=True,
        mode="755",
    )

    sysctl_content = "\n".join(
        f"{key} = {value}"
        for key, value in sysctl["settings"].items()
    ) + "\n"

    files.put(
        name="Create 99-local.conf with sysctl settings",
        src=io.StringIO(sysctl_content),
        dest="/etc/sysctl.d/99-local.conf",
        _sudo=True,
        mode="644",
    )

    server.shell(
        name="Apply sysctl settings",
        commands=["sysctl --system"],
        _sudo=True,
    )
