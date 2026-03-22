# Default configuration for all hosts
# These values can be overridden via --data or group_data files

# User configuration
user = "vscode"

# Runtime environments - enable flags
enable_docker = False
enable_zsh = False
enable_tmux = False
enable_nvm = False
enable_python = False

# Development tools - enable flags
enable_alacritty = False
enable_nvim = False
enable_fzf = False

# Docker configuration
docker = {
    "enable_daemon_config": True,
    "daemon_config_folder": "/etc/docker",
    "enable_compose_alias": True,
}

# Zsh configuration
zsh = {
    "enable_zsh_autosuggestions": True,
    "enable_tmux_autostart": True,
    "theme": "amuse",
    "motd_path": "/etc/profile.d/update-motd.sh",
    "completions_dir": "~/zsh/completions",
    "homebrew_path": "",
    "homebrew_home": "",
}

# Tmux configuration
tmux = {
    "default_shell": "/bin/zsh",
}

# Nvm configuration
nvm = {
    "nvm_version": "v0.40.4",
    "update_scripts_dir": "/usr/local/bin",
    "cleanup_scripts_dir": "/usr/local/bin",
    "projects_dir": None,
}

# Python configuration
python = {
    "venvs": [],
    "pyenv_dir": None,
}

# Alacritty configuration
alacritty = {
    "font_size": 12,
}

# Neovim configuration
nvim = {
    "nvim_repo": "https://github.com/BacLuc/NormalNvim.git",
    "update_scripts_dir": "/usr/local/bin",
}

# Fzf configuration
fzf = {
    "fzf_default_opts": "--tmux",
}
