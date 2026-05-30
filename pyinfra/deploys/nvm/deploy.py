import io

from pyinfra import host
from pyinfra.operations import files, server

user = host.data.get("user", "ubuntu")

nvm = {
    # renovate: datasource=github-releases depName=nvm-sh/nvm
    "nvm_version": "v0.40.4",
    **host.data.nvm,
}

if host.data.nvm["enabled"]:
    server.shell(
        name="Setup nvm",
        commands=f"curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/{nvm['nvm_version']}/install.sh | bash",
    )

    files.block(
        name="Add nvm to path in bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add nvm to PATH",
        content=f'export NVM_DIR="$HOME/.nvm"\n[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"\n[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"',
        try_prevent_shell_expansion=True,
    )

    if host.data.zsh["enabled"]:
        files.block(
            name="Add nvm to path in zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: add nvm to PATH",
            content=f'export NVM_DIR="$HOME/.nvm"\n[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"\n[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"',
            try_prevent_shell_expansion=True,
        )

    nvm_upgrade = f"#!/bin/sh\nset -e\n\nuser=\"{user}\"\nnvm_version={nvm['nvm_version']}\n\nsu \"$user\" -c \"git -C /home/{user}/.nvm fetch --tags\"\nsu \"$user\" -c \"git -C /home/{user}/.nvm reset --hard $nvm_version\"\n"
    files.put(
        name="Add script to update nvm",
        src=io.StringIO(nvm_upgrade),
        dest=f"{host.data.update_packages_script['dir']}/nvm-upgrade",
        mode="755",
        _sudo=True,
    )

    node_modules_cleanup = f"#!/bin/sh\n\ncleanup_node_modules() {{\n    root=$1\n    for nm_dir in $(find $root \\\n      -type d -name node_modules \\\n      -atime \"+21\" \\\n      | grep -E -v '.*/node_modules/.*/node_modules(/|$)'); do\n      du -h -d0 $nm_dir\n      rm -rf $nm_dir\n    done\n}}\n\ncleanup_node_modules /home/{user}/projects\n"
    files.put(
        name="Add node modules cleanup script",
        src=io.StringIO(node_modules_cleanup),
        dest=f"{host.data.cleanup_scripts['dir']}/cleanup-node-modules",
        mode="755",
        _sudo=True,
    )

    node_versions_cleanup = f"#!/bin/sh\n\nroot=/home/{user}/.nvm/versions/node/\nfor nm_dir in $(find $root \\\n  -mindepth 1 -maxdepth 1 \\\n  -type d \\\n  -atime \"+200\"); do\n  du -h -d0 $nm_dir\n  rm -rf $nm_dir\ndone\n"
    files.put(
        name="Add node versions cleanup script",
        src=io.StringIO(node_versions_cleanup),
        dest=f"{host.data.cleanup_scripts['dir']}/cleanup-node-versions",
        mode="755",
        _sudo=True,
    )
