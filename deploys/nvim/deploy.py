from pyinfra import host
from pyinfra.facts.files import Directory, File
from pyinfra.operations import files, server

from operations.filesystem import dirname_of
from operations.homebrew import HOMEBREW_BIN, user_brew_bin
from operations.user import get_user_name

user = get_user_name()

if host.data.nvim["enabled"]:
    nvim_bin = f"{HOMEBREW_BIN}/nvim"
    nvim_config_dir = f"/home/{user}/.config/nvim"

    server.shell(
        name="Install neovim via brew",
        commands=[user_brew_bin(user) + " install neovim"],
        _if=lambda: host.get_fact(File, nvim_bin) is None,
    )

    server.shell(
        name="Remove stale neovim config directory",
        commands=[f"rm -rf {nvim_config_dir}"],
        _sudo=True,
        _if=lambda: host.get_fact(Directory, nvim_config_dir) is not None,
    )

    files.put(
        name="Deploy minimal nvim init.lua",
        src=f"{dirname_of(__file__)}/files/init.lua",
        dest=f"{nvim_config_dir}/init.lua",
        user=user,
        group=user,
        mode="644",
        create_remote_dir=True,
    )

    server.shell(
        name="Set nvim as default vim and vi alternative",
        commands=[
            f"update-alternatives --install /usr/bin/vim vim {nvim_bin} 1 || true",
            f"update-alternatives --set vim {nvim_bin}",
            f"update-alternatives --install /usr/bin/vi vi {nvim_bin} 1 || true",
            f"update-alternatives --set vi {nvim_bin}",
        ],
        _sudo=True,
    )
