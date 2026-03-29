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
    configure_ai_agent_devcontainer,
    configure_alacritty,
    configure_devcontainer_cli,
    configure_fzf,
    configure_nvim,
    configure_zed,
)
from pyinfra_collections.applications import (
    configure_displaylink_driver,
    configure_intellij,
    configure_okular,
    configure_ubuntu_desktop,
)
from pyinfra_collections.runtime_environments import (
    configure_backup_burp,
    configure_basicsetup,
    configure_docker,
    configure_fluxcd,
    configure_git_lfs,
    configure_hashicorp_vault_cli,
    configure_homebrew,
    configure_kubectl,
    configure_lazygit,
    configure_nvm,
    configure_ollama,
    configure_openwebui,
    configure_php_development,
    configure_python,
    configure_sysctl,
    configure_tmux,
    configure_ubuntu_cleanup,
    configure_update_packages_script,
    configure_vagrant,
    configure_vshn_emergency_credentials_receive,
    configure_vshn_tools,
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

# Sysctl
if should_run("sysctl", "enable_sysctl"):
    configure_sysctl(_sudo=True)

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

# Git LFS
if should_run("git_lfs", "enable_git_lfs"):
    configure_git_lfs(_sudo=True)

# Ollama
if should_run("ollama", "enable_ollama"):
    configure_ollama(_sudo=True)

# Zed
if should_run("zed", "enable_zed"):
    configure_zed(_sudo=True)

# DevContainer CLI
if should_run("devcontainer_cli", "enable_devcontainer_cli"):
    configure_devcontainer_cli(_sudo=True)

# Basic Setup
if should_run("basicsetup", "enable_basicsetup"):
    configure_basicsetup(_sudo=True)

# HashiCorp Vault CLI
if should_run("hashicorp_vault_cli", "enable_hashicorp_vault_cli"):
    configure_hashicorp_vault_cli(_sudo=True)

# Vagrant
if should_run("vagrant", "enable_vagrant"):
    configure_vagrant(_sudo=True)

# Update Packages Script
if should_run("update_packages_script", "enable_update_packages_script"):
    configure_update_packages_script(_sudo=True)

# FluxCD
if should_run("fluxcd", "enable_fluxcd"):
    configure_fluxcd(_sudo=True)

# PHP Development
if should_run("php_development", "enable_php_development"):
    configure_php_development(_sudo=True)

# OpenWebUI
if should_run("openwebui", "enable_openwebui"):
    configure_openwebui(_sudo=True)

# Okular
if should_run("okular", "enable_okular"):
    configure_okular(_sudo=True)

# IntelliJ / JetBrains
if should_run("jetbrains", "enable_jetbrains"):
    configure_intellij(_sudo=True)

# DisplayLink Driver
if should_run("displaylink_driver", "enable_displaylink_driver"):
    configure_displaylink_driver(_sudo=True)

# Ubuntu Desktop
if should_run("ubuntu_desktop", "enable_ubuntu_desktop"):
    configure_ubuntu_desktop(_sudo=True)

# VSHN Tools
if should_run("vshn_tools", "enable_vshn_tools"):
    configure_vshn_tools(_sudo=True)

# Ubuntu Cleanup
if should_run("ubuntu_cleanup", "enable_ubuntu_cleanup"):
    configure_ubuntu_cleanup(_sudo=True)

# AI Agent DevContainer
if should_run("ai_agent_devcontainer", "enable_ai_agent_devcontainer"):
    configure_ai_agent_devcontainer(_sudo=True)

# VSHN Emergency Credentials Receive
if should_run("vshn_emergency_credentials_receive", "enable_vshn_emergency_credentials_receive"):
    configure_vshn_emergency_credentials_receive(_sudo=True)

# Backup Burp
if should_run("backup_burp", "enable_backup_burp"):
    configure_backup_burp(_sudo=True)
