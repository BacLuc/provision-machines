"""Nvm (Node Version Manager) setup and configuration."""

import os
from io import StringIO

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import files, server


@deploy("Nvm")
def configure_nvm(
    user=None,
    home=None,
    nvm_version="v0.40.4",
    enable_zsh=False,
    update_scripts_dir="/usr/local/bin",
    cleanup_scripts_dir="/usr/local/bin",
    projects_dir=None,
    _sudo=None,
    **kwargs,
):
    """Setup Nvm (Node Version Manager) with shell integration."""
    if not host.data.get("enable_nvm", False):
        return

    # Get user/home from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    if home is None:
        home = f"/home/{user}"

    if projects_dir is None:
        projects_dir = f"{home}/projects"

    nvm_dir = f"{home}/.nvm"

    # Install nvm via curl (only if not already installed)
    server.shell(
        name="Install nvm",
        commands=[
            f"test -d {nvm_dir} || curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/{nvm_version}/install.sh | bash"
        ],
    )

    # Add nvm to PATH for bash
    bashrc_content = """
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"
"""

    files.block(
        name="Add nvm to PATH for bash",
        path=f"{home}/.bashrc",
        content=bashrc_content,
        marker="# {mark} ANSIBLE MANAGED BLOCK: add nvm to PATH",
    )

    # Add nvm to PATH for zsh if enabled
    if enable_zsh:
        files.block(
            name="Add nvm to PATH for zsh",
            path=f"{home}/.zshrc",
            content=bashrc_content,
            marker="# {mark} ANSIBLE MANAGED BLOCK: add nvm to PATH",
        )

    # Add nvm update script
    update_script_content = f"""#!/bin/sh
set -e

user="{user}"
nvm_version={nvm_version}

su "$user" -c "git -C /home/{user}/.nvm fetch --tags"
su "$user" -c "git -C /home/{user}/.nvm reset --hard $nvm_version"
"""

    files.put(
        name="Add nvm update script",
        src=StringIO(update_script_content),
        dest=f"{update_scripts_dir}/nvm-upgrade",
        mode="755",
    )

    # Add node_modules cleanup script
    cleanup_node_modules_content = f"""#!/bin/sh

cleanup_node_modules() {{
    root=$1
    for nm_dir in $(find $root \\
      -type d -name node_modules \\
      -atime "+21" \\
      | grep -E -v '.*/node_modules/.*/node_modules(/|$)'); do
      du -h -d0 $nm_dir
      rm -rf $nm_dir
    done
}}

cleanup_node_modules {projects_dir}
"""

    files.put(
        name="Add node_modules cleanup script",
        src=StringIO(cleanup_node_modules_content),
        dest=f"{cleanup_scripts_dir}/cleanup-node-modules",
        mode="755",
    )
