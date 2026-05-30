import io

from pyinfra import host
from pyinfra.operations import files, server

user = host.data.get("user", "ubuntu")

if host.data.nvim["enabled"]:
    homebrew_binaries_path = host.data.homebrew.get("binaries_path", "/home/linuxbrew/.linuxbrew/bin")

    server.shell(
        name="Install neovim",
        commands=[f"{homebrew_binaries_path}/brew install neovim"],
    )

    server.shell(
        name="Install NormalNeovim distribution",
        commands=[
            "rm -rf ~/.config/nvim",
            "git clone https://github.com/BacLuc/NormalNvim.git ~/.config/nvim",
        ],
    )

    nvim_upgrade = (
        "#!/bin/sh\n"
        f'user="{user}"\n'
        "version=origin/main\n"
        "\n"
        f'su "$user" -c "git -C /home/{user}/.config/nvim fetch"\n'
        f'su "$user" -c "git -C /home/{user}/.config/nvim reset --hard $version"\n'
    )
    files.put(
        name="Add script to update nvim",
        src=io.StringIO(nvim_upgrade),
        dest=f"{host.data.update_packages_script['dir']}/normal-neovim-upgrade",
        mode="755",
        _sudo=True,
    )

    server.shell(
        name="Add nvim to update-alternatives",
        commands=[
            f"update-alternatives --install /usr/bin/vim vim {homebrew_binaries_path}/nvim 1 || true",
            f"update-alternatives --set vim {homebrew_binaries_path}/nvim || true",
            f"update-alternatives --install /usr/bin/vi vi {homebrew_binaries_path}/nvim 1 || true",
            f"update-alternatives --set vi {homebrew_binaries_path}/nvim || true",
        ],
        _sudo=True,
    )
