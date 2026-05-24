from pyinfra import host
from pyinfra.operations import files, server

user = host.data.get("user", "ubuntu")

nvm_defaults = {
    # renovate: datasource=github-releases depName=nvm-sh/nvm
    "nvm_version": "v0.40.4",
}

nvm = nvm_defaults.copy()
if host.data.get("nvm"):
    nvm.update(host.data.get("nvm", {}))

if (host.data.get("basic_utils", {}).get("enable_nvm", False) or 
    host.data.get("enable_nvm", False)):
    
    nvm_dir = f"/home/{user}/.nvm"
    
    files.file(
        name="Check if nvm is already installed",
        path=nvm_dir,
        _sudo=False,
    )
    
    server.shell(
        name="Setup nvm",
        commands=f"curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/{nvm['nvm_version']}/install.sh | bash",
    )
    
    files.block(
        name="Add nvm to path for bash",
        path=f"/home/{user}/.bashrc",
        marker="# PYINFRA MANAGED BLOCK: add nvm to PATH",
        block=f"""export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion\"""",
    )
    
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Add nvm to path for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# PYINFRA MANAGED BLOCK: add nvm to PATH",
            block=f"""export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion\"""",
        )
    
    files.put(
        name="Add script to update nvm",
        dest=f"{host.data.get('update_packages_script', {}).get('dir', '/usr/local/bin')}/nvm-upgrade",
        content=f"""#!/bin/sh
set -e

user="{user}"
nvm_version={nvm['nvm_version']}

su "$user" -c "git -C /home/{user}/.nvm fetch --tags"
su "$user" -c "git -C /home/{user}/.nvm reset --hard $nvm_version"
""",
        mode="755",
        _sudo=True,
    )
    
    files.put(
        name="Add node modules cleanup script",
        dest=f"{host.data.get('cleanup_scripts', {}).get('dir', '/usr/local/bin/cleanup_scripts.d')}/cleanup-node-modules",
        content=f"""#!/bin/sh

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
""",
        mode="755",
        _sudo=True,
    )
    
    files.put(
        name="Add node versions cleanup script",
        dest=f"{host.data.get('cleanup_scripts', {}).get('dir', '/usr/local/bin/cleanup_scripts.d')}/cleanup-node-versions",
        content=f"""#!/bin/sh

root=/home/{user}/.nvm/versions/node/
for nm_dir in $(find $root \\
  -mindepth 1 -maxdepth 1 \\
  -type d \\
  -atime "+200"); do
  du -h -d0 $nm_dir
  rm -rf $nm_dir
done
""",
        mode="755",
        _sudo=True,
    )