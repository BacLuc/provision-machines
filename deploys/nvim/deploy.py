import io

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import files, git, server

from operations.homebrew import HOMEBREW_BIN, user_brew_bin
from operations.user import get_user_name

user = get_user_name()

if host.data.nvim["enabled"]:
    nvim_bin = f"{HOMEBREW_BIN}/nvim"

    server.shell(
        name="Install neovim via brew",
        commands=[user_brew_bin(user) + " install neovim"],
        _if=lambda: host.get_fact(File, nvim_bin) is None,
    )

    git.repo(
        name="Install NormalNvim distribution",
        src="https://github.com/BacLuc/NormalNvim.git",
        dest=f"/home/{user}/.config/nvim",
        user=user,
        group=user,
    )

    files.put(
        name="Add script to update nvim",
        src=io.StringIO(
            f"""user="{user}"
version=origin/main

su "$user" -c "git -C /home/{user}/.config/nvim fetch"
su "$user" -c "git -C /home/{user}/.config/nvim reset --hard $version"
"""
        ),
        dest=f"{host.data.update_packages_script['dir']}/normal-neovim-upgrade",
        _sudo=True,
        mode="755",
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
