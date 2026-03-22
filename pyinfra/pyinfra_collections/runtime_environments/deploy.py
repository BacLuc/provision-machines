"""
Pyinfra deploy for runtime_environments.

This script sets up various runtime environments like shells and container runtimes.

Usage:
    pyinfra @local deploy.py
    pyinfra @local deploy.py --data "user=username"
"""

import os

from pyinfra.context import host

from pyinfra_collections.runtime_environments import (
    configure_docker,
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


# Get configuration from host.data with defaults
user = host.data.get("user") or os.environ.get("USER", "vscode")
home = f"/home/{user}"

# Get enable flags
enable_zsh = parse_bool(host.data.get("enable_zsh", False))
enable_docker = parse_bool(host.data.get("enable_docker", False))
enable_tmux = parse_bool(host.data.get("enable_tmux", False))
enable_nvm = parse_bool(host.data.get("enable_nvm", False))
enable_python = parse_bool(host.data.get("enable_python", False))

# Get zsh configuration
zsh_config = host.data.get("zsh", {})
enable_zsh_autosuggestions = parse_bool(zsh_config.get("enable_zsh_autosuggestions", True))
enable_tmux_autostart = parse_bool(zsh_config.get("enable_tmux_autostart", True))
theme = zsh_config.get("theme", "amuse")
motd_path = zsh_config.get("motd_path", "/etc/profile.d/update-motd.sh")
completions_dir = zsh_config.get("completions_dir", "~/zsh/completions")
homebrew_path = zsh_config.get("homebrew_path", "")
homebrew_home = zsh_config.get("homebrew_home", "")

# Get docker configuration
docker_config = host.data.get("docker", {})
enable_daemon_config = parse_bool(docker_config.get("enable_daemon_config", True))
daemon_config_folder = docker_config.get("daemon_config_folder", "/etc/docker")
enable_compose_alias = parse_bool(docker_config.get("enable_compose_alias", True))

# Get tmux configuration
tmux_config = host.data.get("tmux", {})
default_shell = tmux_config.get("default_shell", "/bin/zsh")

# Get nvm configuration
nvm_config = host.data.get("nvm", {})
nvm_version = nvm_config.get("nvm_version", "v0.40.4")
nvm_update_scripts_dir = nvm_config.get("update_scripts_dir", "/usr/local/bin")
nvm_cleanup_scripts_dir = nvm_config.get("cleanup_scripts_dir", "/usr/local/bin")
projects_dir = nvm_config.get("projects_dir")

# Get python configuration
python_config = host.data.get("python", {})
venvs = python_config.get("venvs", [])
pyenv_dir = python_config.get("pyenv_dir")

# Setup Zsh if enabled
if enable_zsh:
    configure_zsh(
        user=user,
        home=home,
        enable_zsh_autosuggestions=enable_zsh_autosuggestions,
        enable_tmux_autostart=enable_tmux_autostart,
        theme=theme,
        motd_path=motd_path,
        completions_dir=completions_dir,
        homebrew_path=homebrew_path,
        homebrew_home=homebrew_home,
    )

# Setup Docker if enabled
if enable_docker:
    configure_docker(
        user=user,
        home=home,
        enable_daemon_config=enable_daemon_config,
        daemon_config_folder=daemon_config_folder,
        enable_compose_alias=enable_compose_alias,
    )

# Setup Tmux if enabled
if enable_tmux:
    configure_tmux(
        user=user,
        home=home,
        default_shell=default_shell,
    )

# Setup Nvm if enabled
if enable_nvm:
    configure_nvm(
        user=user,
        home=home,
        nvm_version=nvm_version,
        enable_zsh=enable_zsh,
        update_scripts_dir=nvm_update_scripts_dir,
        cleanup_scripts_dir=nvm_cleanup_scripts_dir,
        projects_dir=projects_dir,
    )

# Setup Python if enabled
if enable_python:
    configure_python(
        user=user,
        home=home,
        venvs=venvs,
        pyenv_dir=pyenv_dir,
    )
