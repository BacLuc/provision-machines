import io

from pyinfra.facts.files import Directory

from operations.user import get_user_name
from pyinfra import host
from pyinfra.operations import files, server

user = get_user_name()

if host.data.nvm["enabled"]:
    nvm = host.data.nvm
    install_nvm = server.shell(
        name="Setup nvm",
        commands=f"curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/{nvm['nvm_version']}/install.sh | bash",
        _if=lambda: host.get_fact(Directory, f"/home/{user}/.nvm") is None,
    )

    files.block(
        name="Add nvm to path in bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add nvm to PATH",
        content="""\
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"\
""",
        try_prevent_shell_expansion=True,
    )

    if host.data.zsh["enabled"]:
        files.block(
            name="Add nvm to path in zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: add nvm to PATH",
            content="""\
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"\
""",
            try_prevent_shell_expansion=True,
        )

    server.shell(
        name="install latest lts",
        commands=f"source /home/{user}/.nvm/nvm.sh; nvm install --lts --default",
        _shell_executable="/bin/bash",
        _if=lambda: install_nvm.executed and install_nvm.did_succeed(),
    )

    nvm_upgrade = f"""#!/bin/sh
set -e

user="{user}"
nvm_version={nvm["nvm_version"]}

su "$user" -c "git -C /home/{user}/.nvm fetch --tags"
su "$user" -c "git -C /home/{user}/.nvm reset --hard $nvm_version"
"""
    files.put(
        name="Add script to update nvm",
        src=io.StringIO(nvm_upgrade),
        dest=f"{host.data.update_packages_script['dir']}/nvm-upgrade",
        mode="755",
        _sudo=True,
    )

    node_modules_cleanup = f"""#!/bin/sh

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

cleanup_node_modules /home/{user}/projects
"""
    files.put(
        name="Add node modules cleanup script",
        src=io.StringIO(node_modules_cleanup),
        dest=f"{host.data.cleanup_scripts['dir']}/cleanup-node-modules",
        mode="755",
        _sudo=True,
    )

    node_versions_cleanup = f"""#!/bin/sh

root=/home/{user}/.nvm/versions/node/
for nm_dir in $(find $root \\
  -mindepth 1 -maxdepth 1 \\
  -type d \\
  -atime "+200"); do
  du -h -d0 $nm_dir
  rm -rf $nm_dir
done
"""
    files.put(
        name="Add node versions cleanup script",
        src=io.StringIO(node_versions_cleanup),
        dest=f"{host.data.cleanup_scripts['dir']}/cleanup-node-versions",
        mode="755",
        _sudo=True,
    )
