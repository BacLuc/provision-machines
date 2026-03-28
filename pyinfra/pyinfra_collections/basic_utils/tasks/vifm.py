"""Vifm file manager configuration."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, files


@deploy("Vifm")
def configure_vifm(user=None, home=None, enable_zsh=False, _sudo=None):
    """Setup vifm file manager."""
    # Install vifm
    apt.packages(
        name="Install vifm",
        packages=["vifm"],
        update=True,
    )

    # Create vifm config directory
    files.directory(
        name="Create vifm config directory",
        path=f"{home}/.config/vifm",
        present=True,
    )

    # Create basic vifmrc
    files.put(
        name="Create vifmrc",
        src="only\n",
        dest=f"{home}/.config/vifm/vifmrc",
        mode="644",
    )

    # Add vicd function to bashrc
    vicd_function = """
vicd() {
    local dst="$(command vifm --choose-dir -)"
    if [ -n "$dst" ]; then
        cd "$dst"
    fi
}
"""
    files.block(
        path=f"{home}/.bashrc",
        content=vicd_function,
        marker="# {mark} PYINFRA MANAGED: vicd function",
    )

    if enable_zsh:
        files.block(
            path=f"{home}/.zshrc",
            content=vicd_function,
            marker="# {mark} PYINFRA MANAGED: vicd function",
        )
