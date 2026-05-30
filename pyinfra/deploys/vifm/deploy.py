import io

from pyinfra import host
from pyinfra.operations import apt, files

user = host.data.get("user", "ubuntu")

vicd_function = """vicd() {
    local dst="$(command vifm --choose-dir - "$@")"
    if [ -z "$dst" ]; then
        echo 'Directory picking cancelled/failed'
        return 1
    fi
    cd "$dst"
}"""

if host.data.vifm["enabled"]:
    apt.packages(
        name="Install vifm",
        packages=["vifm"],
        _sudo=True,
    )

    files.put(
        name="Provision vifmrc",
        src=io.StringIO("only"),
        dest=f"/home/{user}/.vifm/vifmrc",
        mode="644",
    )

    files.block(
        name="Add vicd command to bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: vicd",
        content=vicd_function,
    )

    if host.data.zsh["enabled"]:
        files.block(
            name="Add vicd command to zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: vicd",
            content=vicd_function,
        )
