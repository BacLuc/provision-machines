# Runtime environments - enable for laptop
enable_docker = True
enable_zsh = True
enable_tmux = True
enable_nvm = True
enable_python = True

# Development tools - enable for laptop
enable_alacritty = True
enable_nvim = True
enable_fzf = True

# Python configuration for laptop
python = {
    "venvs": [
        {
            "name": "dev",
            "python_version": "3.11",
        },
        {
            "name": "ml",
            "python_version": "3.10",
        },
    ],
    "pyenv_dir": None,
}

# Debug settings
debug = False
verbose = False
