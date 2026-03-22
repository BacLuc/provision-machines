"""Neovim editor setup and configuration."""

import os
from io import StringIO

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, files, git, server


@deploy("Neovim")
def configure_nvim(
    user=None,
    home=None,
    homebrew_path="",
    homebrew_home="",
    nvim_repo="https://github.com/BacLuc/NormalNvim.git",
    update_scripts_dir="/usr/local/bin",
    _sudo=None,
    **kwargs,
):
    """Setup Neovim editor with NormalNvim distribution."""
    if not host.data.get("enable_nvim", False):
        return

    # Get user/home from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    if home is None:
        home = f"/home/{user}"

    # Get config from host.data
    nvim_config = host.data.get("nvim", {})
    if not nvim_repo:
        nvim_repo = nvim_config.get("nvim_repo", "https://github.com/BacLuc/NormalNvim.git")
    if not update_scripts_dir:
        update_scripts_dir = nvim_config.get("update_scripts_dir", "/usr/local/bin")

    # Install neovim via homebrew if paths are provided
    if homebrew_home:
        nvim_bin = f"{homebrew_home}/.linuxbrew/bin/nvim"
        server.shell(
            name="Install neovim via homebrew",
            commands=["~/bin/brew install neovim"],
        )
    elif homebrew_path:
        nvim_bin = f"{homebrew_path}/nvim"
    else:
        # Fallback: install via apt
        apt.packages(
            name="Install neovim via apt",
            packages=["neovim"],
            update=True,
        )
        nvim_bin = "/usr/bin/nvim"

    # Clone NormalNvim configuration
    git.repo(
        name="Clone NormalNvim configuration",
        src=nvim_repo,
        dest=f"{home}/.config/nvim",
        user=user,
        group=user,
    )

    # Create update script
    update_script_content = f"""#!/bin/sh
set -e

user="{user}"
version=origin/main

su "$user" -c "git -C /home/{user}/.config/nvim fetch"
su "$user" -c "git -C /home/{user}/.config/nvim reset --hard $version"
"""

    files.put(
        name="Add nvim update script",
        src=StringIO(update_script_content),
        dest=f"{update_scripts_dir}/normal-neovim-upgrade",
        mode="755",
    )

    # Setup vim alternative to point to nvim
    server.shell(
        name="Add vim alternative for nvim",
        commands=[f"update-alternatives --install /usr/bin/vim vim {nvim_bin} 1 || true"],
    )

    server.shell(
        name="Set nvim as default vim",
        commands=[f"update-alternatives --set vim {nvim_bin} || true"],
    )

    # Setup vi alternative to point to nvim
    server.shell(
        name="Add vi alternative for nvim",
        commands=[f"update-alternatives --install /usr/bin/vi vi {nvim_bin} 1 || true"],
    )

    server.shell(
        name="Set nvim as default vi",
        commands=[f"update-alternatives --set vi {nvim_bin} || true"],
    )
