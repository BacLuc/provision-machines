# CI-specific configuration overrides
# Applied when deploying with --limit ci

import os

# User configuration
user = os.environ.get("USER", "runner")

# Runtime environments - enable all for CI testing
enable_basicsetup = True
enable_docker = True
enable_git_lfs = True
enable_hashicorp_vault_cli = True
enable_homebrew = True
enable_kubectl = True
enable_lazygit = True
enable_nvm = True
enable_ollama = True
enable_python = True
enable_sysctl = True
enable_tmux = True
enable_update_packages_script = True
enable_vagrant = True
enable_zsh = True

# Development tools - enable all for CI testing
enable_alacritty = True
enable_nvim = True
enable_fzf = True
enable_zed = True
enable_devcontainer_cli = True

# Basic utils - enable for CI testing
enable_direnv = True
enable_keepassxc = True
enable_signal = True
enable_ssh_config_dir = True
ssh_agent = True
ssh_key_filename = "id_ed25519"
ssh_key_comment = "ssh-key"
gcr_ssh_agent = True
gcr_ssh_agent_socket = "/run/user/1000/gcr/ssh"
enable_java = True
sdkman_tools = []
enable_flutter = True
remove_ghostty = True
enable_openvpn = True
enable_rambox = True
enable_zoom = True
enable_go = True
enable_bat = True
enable_python_basic_utils = True
python_venvs = []

# Python configuration for CI
python = {
    "venvs": [
        {
            "name": "test",
            "python_version": "3.11",
        }
    ],
    "pyenv_dir": None,
}

# Debug settings for CI
debug = True
verbose = True
