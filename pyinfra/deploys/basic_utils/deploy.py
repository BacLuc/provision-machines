from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
    server,
)

# Get user from host data
user = host.data.get("user", "ubuntu")

# Set defaults for basic_utils role
basic_utils_defaults = {
    "ssh_key": {
        "filename": "id_ed25519",
    },
    "ssh_agent": {},
    "gcr_ssh_agent": {
        "socket": f"/run/user/{host.data.get('user_id', '1000')}/gcr/ssh",
    },
    "python": {
        "venvs": [],
    },
}

# Combine defaults with host data
basic_utils = basic_utils_defaults.copy()
if host.data.get("basic_utils"):
    basic_utils.update(host.data.get("basic_utils", {}))

# Setup user bin dir
files.directory(
    name="Setup user bin dir",
    path=f"/home/{user}/bin",
    user=user,
    group=user,
    mode="755",
)

# Source user bin and ~/.local/bin dir in bash
files.block(
    name="Source user bin and ~/.local/bin dir in bash",
    path=f"/home/{user}/.bashrc",
    marker="# ANSIBLE MANAGED BLOCK: bin of user",
    content=f"export PATH=\"/home/{user}/bin:/home/{user}/.local/bin:$PATH\"",
    user=user,
    group=user,
)

# Source user bin and ~/.local/bin dir in zsh if zsh is enabled
if host.data.get("zsh", {}).get("enabled", False):
    files.block(
        name="Source user bin and ~/.local/bin dir in zsh",
        path=f"/home/{user}/.zshrc",
        marker="# ANSIBLE MANAGED BLOCK: bin of user",
        content=f"export PATH=\"/home/{user}/bin:/home/{user}/.local/bin:$PATH\"",
        user=user,
        group=user,
    )

# Setup direnv if enabled
if basic_utils.get("enable_direnv", False):
    # Install direnv package
    apt.packages(
        name="Install direnv package",
        packages=["direnv"],
        _sudo=True,
    )

    # Source direnv bash
    files.block(
        name="Source direnv bash",
        path=f"/home/{user}/.bashrc",
        marker="# ANSIBLE MANAGED BLOCK: source direnv",
        content="eval \"$(direnv hook bash)\"",
        user=user,
        group=user,
    )

    # Source direnv zsh if zsh is enabled
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Source direnv zsh",
            path=f"/home/{user}/.zshrc",
            marker="# ANSIBLE MANAGED BLOCK: source direnv",
            content="eval \"$(direnv hook zsh)\"",
            user=user,
            group=user,
        )

# Install keepassxc flatpak if enabled
if basic_utils.get("enable_keepassxc", False):
    # Install KeePassXC via flatpak
    # Note: flatpak operations would need to be implemented separately
    # as pyinfra doesn't have direct flatpak support
    
    # Add ssh agent integration if enabled
    if basic_utils.get("gcr_ssh_agent", {}).get("enable", False):
        # Configure ssh-agent sock
        files.block(
            name="Configure ssh-agent sock",
            path=f"/home/{user}/.var/app/org.keepassxc.KeePassXC/cache/keepassxc/keepassxc.ini",
            marker="# ANSIBLE MANAGED BLOCK: configure ssh-agent",
            content=f"AuthSockOverride={basic_utils.get('gcr_ssh_agent', {}).get('socket', '')}",
            user=user,
            group=user,
        )

# Install signal snap if enabled
if basic_utils.get("enable_signal", False):
    # Note: snap operations would need to be implemented separately
    # as pyinfra doesn't have direct snap support
    pass

# Setup ssh config dir if enabled
if basic_utils.get("enable_ssh_config_dir", False):
    files.directory(
        name="Setup ssh config dir",
        path=f"/home/{user}/.ssh/config.d",
        user=user,
        group=user,
        mode="700",
    )

# Setup ssh-agent if enabled
if (basic_utils.get("ssh_key", {}).get("enable", False) and 
    basic_utils.get("ssh_agent", {}).get("enable", False)):
    
    # Setup ssh-agent for bash
    files.block(
        name="Setup ssh-agent for bash",
        path=f"/home/{user}/.bashrc",
        marker="# ANSIBLE MANAGED BLOCK: start ssh agent",
        content=f"""if [ -z "$(pgrep ssh-agent)" ]; then
  rm -rf /tmp/ssh-*
  eval $(ssh-agent -s) > /dev/null
fi
export SSH_AGENT_PID=$(pgrep ssh-agent)
export SSH_AUTH_SOCK=$(find /tmp/ssh-* -name 'agent.*')

if [[ ! $(ssh-add -l | grep "{basic_utils.get('ssh_key', {}).get('comment', '')}") ]]; then
  ssh_key_path="$HOME/.ssh/{basic_utils.get('ssh_key', {}).get('filename', '')}"
  if [[ -f "$ssh_key_path" ]]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
        user=user,
        group=user,
    )

    # Setup ssh-agent for zsh if zsh is enabled
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Setup ssh-agent for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# ANSIBLE MANAGED BLOCK: start ssh agent",
            content=f"""if [ -z "$(pgrep ssh-agent)" ]; then
  rm -rf /tmp/ssh-*
  eval $(ssh-agent -s) > /dev/null
fi
export SSH_AGENT_PID=$(pgrep ssh-agent)
export SSH_AUTH_SOCK=$(find /tmp/ssh-* -name 'agent.*')

if [[ ! $(ssh-add -l | grep "{basic_utils.get('ssh_key', {}).get('comment', '')}") ]]; then
  ssh_key_path="$HOME/.ssh/{basic_utils.get('ssh_key', {}).get('filename', '')}"
  if [[ -f "$ssh_key_path" ]]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
            user=user,
            group=user,
        )

# Setup gcr-ssh-agent if enabled
if basic_utils.get("gcr_ssh_agent", {}).get("enable", False):
    # Setup gcr-ssh-agent for bash
    files.block(
        name="Setup gcr-ssh-agent for bash",
        path=f"/home/{user}/.bashrc",
        marker="# ANSIBLE MANAGED BLOCK: start gcr ssh agent",
        content=f"""export SSH_AUTH_SOCK={basic_utils.get('gcr_ssh_agent', {}).get('socket', '')}

if [[ ! $(ssh-add -l | grep "{basic_utils.get('ssh_key', {}).get('comment', '')}") ]]; then
  ssh_key_path="$HOME/.ssh/{basic_utils.get('ssh_key', {}).get('filename', '')}"
  if [[ -f "$ssh_key_path" ]]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
        user=user,
        group=user,
    )

    # Setup gcr-ssh-agent for zsh if zsh is enabled
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Setup gcr-ssh-agent for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# ANSIBLE MANAGED BLOCK: start gcr ssh agent",
            content=f"""export SSH_AUTH_SOCK={basic_utils.get('gcr_ssh_agent', {}).get('socket', '')}

if [[ ! $(ssh-add -l | grep "{basic_utils.get('ssh_key', {}).get('comment', '')}") ]]; then
  ssh_key_path="$HOME/.ssh/{basic_utils.get('ssh_key', {}).get('filename', '')}"
  if [[ -f "$ssh_key_path" ]]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
            user=user,
            group=user,
        )

# Setup SDKMAN if Java is enabled
if basic_utils.get("enable_java", False):
    # Add sdkman to .bashrc
    files.block(
        name="Add sdkman to .bashrc",
        path=f"/home/{user}/.bashrc",
        marker="# ANSIBLE MANAGED BLOCK: sdkman-init",
        content="""export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh\"""",
        user=user,
        group=user,
    )

    # Add sdkman to .zshrc if zsh is enabled
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Add sdkman to .zshrc",
            path=f"/home/{user}/.zshrc",
            marker="# ANSIBLE MANAGED BLOCK: sdkman-init",
            content="""export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh\"""",
            user=user,
            group=user,
        )

# Flutter development if enabled
if basic_utils.get("enable_flutter", False):
    # Add fvm to path for bash
    files.block(
        name="Add fvm to path for bash",
        path=f"/home/{user}/.bashrc",
        marker="# ANSIBLE MANAGED BLOCK: add fvm to PATH",
        content=f"export PATH=\"/home/{user}/.fvm_flutter/bin:$PATH\"",
        user=user,
        group=user,
    )

    # Add fvm to path for zsh if zsh is enabled
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Add fvm to path for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# ANSIBLE MANAGED BLOCK: add fvm to PATH",
            content=f"export PATH=\"/home/{user}/.fvm_flutter/bin:$PATH\"",
            user=user,
            group=user,
        )

    # Add docker user to kvm group
    # Note: This would need to be implemented with user and group operations

# Enable openvpn file import for network manager if enabled
if basic_utils.get("enable_openvpn_config_import_network_manager", False):
    apt.packages(
        name="Install openvpn packages",
        packages=["network-manager-openvpn", "network-manager-openvpn-gnome"],
        _sudo=True,
    )

# Install rambox if enabled
if basic_utils.get("enable_rambox", False):
    # Note: snap operations would need to be implemented separately
    # as pyinfra doesn't have direct snap support
    pass

# Install zoom flatpak if enabled
if basic_utils.get("enable_zoom", False):
    # Note: flatpak operations would need to be implemented separately
    # as pyinfra doesn't have direct flatpak support
    pass

# Setup go if enabled
if basic_utils.get("enable_go", False):
    # Setup goenv for bash
    files.block(
        name="Setup goenv for bash",
        path=f"/home/{user}/.bashrc",
        marker="# ANSIBLE MANAGED BLOCK: add goenv",
        content="""export GOENV_ROOT="$HOME/.goenv
eval "$($HOME/.goenv/bin/goenv init -)"\""",
        user=user,
        group=user,
    )

    # Setup goenv for zsh if zsh is enabled
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Setup goenv for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# ANSIBLE MANAGED BLOCK: add goenv",
            content="""export GOENV_ROOT="$HOME/.goenv"
export PATH="$GOENV_ROOT/bin:$PATH"
eval "$($HOME/.goenv/bin/goenv init -)"\"""",
            user=user,
            group=user,
        )