import io

from operations.user import get_user_name
from pyinfra import host
from pyinfra.operations import apt, files

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

    vicd = """vicd() {
    local dst="$(command vifm --choose-dir - "$@")"
    if [ -z "$dst" ]; then
        echo "Directory picking cancelled/failed"
        return 1
    fi
    cd "$dst"
}
"""

    files.put(
        name="Add vicd command for bash",
        src=io.StringIO(vicd),
        dest=f"/home/{user}/.bashrc.d/vicd.sh",
        user=user,
        group=user,
        mode="644",
    )

    if host.data.zsh["enabled"]:
        files.put(
            name="Add vicd command for zsh",
            src=io.StringIO(vicd),
            dest=f"/home/{user}/.zshrc.d/vicd.zsh",
            user=user,
            group=user,
            mode="644",
        )
