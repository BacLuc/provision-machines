import io

from pyinfra import host
from pyinfra.operations import apt, files

from operations.user import get_user_name

user = get_user_name()

if host.data.vifm["enabled"]:
    apt.packages(
        name="Install vifm",
        packages=["vifm"],
        _sudo=True,
    )

    files.put(
        name="Provision vifmrc",
        src=io.StringIO("only\n"),
        dest=f"/home/{user}/vifmrc",
        user=user,
        group=user,
        mode="644",
    )
