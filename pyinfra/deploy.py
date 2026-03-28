#!/usr/bin/env python3
"""
Main Pyinfra deployment script.

Usage:
    pyinfra @local deploy.py
    pyinfra @local deploy.py --data enable_zsh=true
    pyinfra @local deploy.py --data "tags=zsh,docker"
"""

from pyinfra.context import host

# Import all configuration functions
from pyinfra_collections.development_tools import (
    configure_alacritty,
    configure_fzf,
    configure_nvim,
)
from pyinfra_collections.runtime_environments import (
    configure_docker,
    configure_homebrew,
    configure_kubectl,
    configure_lazygit,
    configure_nvm,
    configure_python,
    configure_tmux,
    configure_zsh,
)


def parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def should_run(tag, enable_flag):
    """Check if a component should run based on tags or enable flag."""
    tags = host.data.get("tags", "")
    if tags:
        # If tags are specified, only run if tag matches
        tag_list = [t.strip() for t in tags.split(",")]
        return tag in tag_list
    # Otherwise check the enable flag
    return parse_bool(host.data.get(enable_flag, False))


# Docker
if should_run("docker", "enable_docker"):
    configure_docker(_sudo=True)

# Homebrew
if should_run("homebrew", "enable_homebrew"):
    configure_homebrew(_sudo=True)

# Kubectl
if should_run("kubectl", "enable_kubectl"):
    configure_kubectl(_sudo=True)

# Lazygit
if should_run("lazygit", "enable_lazygit"):
    configure_lazygit(_sudo=True)

# NVM/Node.js
if should_run("nvm", "enable_nvm"):
    configure_nvm(_sudo=True)

# Python
if should_run("python", "enable_python"):
    configure_python(_sudo=True)

# Tmux
if should_run("tmux", "enable_tmux"):
    configure_tmux(_sudo=True)

# Zsh
if should_run("zsh", "enable_zsh"):
    configure_zsh(_sudo=True)

# Alacritty
if should_run("alacritty", "enable_alacritty"):
    configure_alacritty(_sudo=True)

# Neovim
if should_run("nvim", "enable_nvim"):
    configure_nvim(_sudo=True)

# FZF
if should_run("fzf", "enable_fzf"):
    configure_fzf(_sudo=True)
