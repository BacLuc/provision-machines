"""
Pyinfra deploy for development_tools.

This script sets up various development tools and IDE configurations.

Usage:
    pyinfra @local deploy.py
    pyinfra @local deploy.py --data "user=username"
"""

import os

from pyinfra.context import host

from pyinfra_collections.development_tools import (
    configure_alacritty,
    configure_fzf,
    configure_nvim,
)


def parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


# Get configuration from host.data with defaults
user = host.data.get("user") or os.environ.get("USER", "vscode")
home = f"/home/{user}"

# Get enable flags
enable_alacritty = parse_bool(host.data.get("enable_alacritty", False))
enable_nvim = parse_bool(host.data.get("enable_nvim", False))
enable_fzf = parse_bool(host.data.get("enable_fzf", False))

# Get alacritty configuration
alacritty_config = host.data.get("alacritty", {})
font_size = alacritty_config.get("font_size", 12)

# Get nvim configuration
nvim_config = host.data.get("nvim", {})
homebrew_path = nvim_config.get("homebrew_path", "")
homebrew_home = nvim_config.get("homebrew_home", "")
nvim_repo = nvim_config.get("nvim_repo", "https://github.com/BacLuc/NormalNvim.git")
update_scripts_dir = nvim_config.get("update_scripts_dir", "/usr/local/bin")

# Get fzf configuration
fzf_config = host.data.get("fzf", {})
fzf_homebrew_path = fzf_config.get("homebrew_path", homebrew_path)
fzf_homebrew_home = fzf_config.get("homebrew_home", homebrew_home)
enable_zsh = parse_bool(fzf_config.get("enable_zsh", False))
fzf_default_opts = fzf_config.get("fzf_default_opts", "--tmux")

# Setup Alacritty if enabled
if enable_alacritty:
    configure_alacritty(user=user, home=home, font_size=font_size)

# Setup Neovim if enabled
if enable_nvim:
    configure_nvim(
        user=user,
        home=home,
        homebrew_path=homebrew_path,
        homebrew_home=homebrew_home,
        nvim_repo=nvim_repo,
        update_scripts_dir=update_scripts_dir,
    )

# Setup Fzf if enabled
if enable_fzf:
    configure_fzf(
        user=user,
        home=home,
        homebrew_path=fzf_homebrew_path,
        homebrew_home=fzf_homebrew_home,
        enable_zsh=enable_zsh,
        fzf_default_opts=fzf_default_opts,
    )
