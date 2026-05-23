from pyinfra import host
from pyinfra.operations import apt, files

user = host.data.get("user", "ubuntu")

if host.data.get("enable_vifm", False):
    
    apt.packages(
        name="Install vifm apt package",
        packages=["vifm"],
        _sudo=True,
    )
    
    files.put(
        name="Provision vifmrc",
        dest=f"/home/{user}/vifmrc",
        content="only",
        mode="644",
    )
    
    vicd_function = """vicd() {
    local dst="$(command vifm --choose-dir - "$@")"
    if [ -z "$dst" ]; then
        echo 'Directory picking cancelled/failed'
        return 1
    fi
    cd "$dst"
}"""
    
    files.block(
        name="Add vicd command to bash",
        path=f"/home/{user}/.bashrc",
        marker="# PYINFRA MANAGED BLOCK: vicd",
        block=vicd_function,
    )
    
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Add vicd command to zsh",
            path=f"/home/{user}/.zshrc",
            marker="# PYINFRA MANAGED BLOCK: vicd",
            block=vicd_function,
        )