"""
Pyinfra deploy for basic_utils.

This replaces the ansible role basic_utils with pyinfra.

Usage:
    pyinfra @local deploy.py
    pyinfra @local deploy.py --data "user=username"
"""

import os

from pyinfra.context import host

from pyinfra_collections.basic_utils.tasks import (
    bat,
    direnv,
    flutter,
    ghostty,
    go,
    java,
    keepassxc,
    openvpn,
    python,
    rambox,
    signal,
    ssh_config,
    user_bin,
    zoom,
)
from pyinfra_collections.basic_utils.tasks import (
    gcr_ssh_agent as gcr_ssh_agent_module,
)
from pyinfra_collections.basic_utils.tasks import (
    ssh_agent as ssh_agent_module,
)


def parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


def main():
    """Main function to setup basic utilities."""
    # Get configuration from host.data with defaults
    user = host.data.user or os.environ.get("USER", "vscode")
    enable_direnv = parse_bool(host.data.get("enable_direnv", False))
    enable_keepassxc = parse_bool(host.data.get("enable_keepassxc", False))
    enable_signal = parse_bool(host.data.get("enable_signal", False))
    enable_ssh_config_dir = parse_bool(host.data.get("enable_ssh_config_dir", False))
    enable_ssh_agent = parse_bool(host.data.get("ssh_agent", False))
    ssh_key_filename = host.data.get("ssh_key_filename", "id_ed25519")
    ssh_key_comment = host.data.get("ssh_key_comment", "ssh-key")
    enable_gcr_ssh_agent = parse_bool(host.data.get("gcr_ssh_agent", False))
    gcr_ssh_agent_socket = host.data.get("gcr_ssh_agent_socket", "/run/user/1000/gcr/ssh")
    enable_java = parse_bool(host.data.get("enable_java", False))
    sdkman_tools = host.data.get("sdkman_tools", [])
    enable_flutter = parse_bool(host.data.get("enable_flutter", False))
    remove_ghostty = parse_bool(host.data.get("remove_ghostty", True))
    enable_openvpn = parse_bool(host.data.get("enable_openvpn", False))
    enable_rambox = parse_bool(host.data.get("enable_rambox", False))
    enable_zoom = parse_bool(host.data.get("enable_zoom", False))
    enable_go = parse_bool(host.data.get("enable_go", False))
    enable_zsh = parse_bool(host.data.get("enable_zsh", False))
    enable_bat = parse_bool(host.data.get("enable_bat", False))
    enable_python = parse_bool(host.data.get("enable_python", False))
    python_venvs = host.data.get("python_venvs", [])
    ssh_config_paths_to_include = host.data.get("ssh_config_paths_to_include", ["./config.d/*"])

    home = f"/home/{user}"

    # Always setup user bin directory and PATH
    user_bin.setup(user=user, home=home)

    # Setup direnv if enabled
    if enable_direnv:
        direnv.setup(user=user, home=home, enable_zsh=enable_zsh)

    # Setup KeePassXC if enabled
    if enable_keepassxc:
        keepassxc.setup(enable_gcr=enable_gcr_ssh_agent, socket_path=gcr_ssh_agent_socket)

    # Setup signal if enabled
    if enable_signal:
        signal.setup()

    # Setup SSH config dir if enabled
    if enable_ssh_config_dir:
        ssh_config.setup(user=user, home=home, paths_to_include=ssh_config_paths_to_include)

    # Setup SSH agent if enabled
    if enable_ssh_agent:
        ssh_agent_module.setup(
            user=user,
            home=home,
            key_filename=ssh_key_filename,
            key_comment=ssh_key_comment,
            enable_zsh=enable_zsh,
        )

    # Setup gcr-ssh-agent if enabled
    if enable_gcr_ssh_agent:
        gcr_ssh_agent_module.setup(
            user=user,
            home=home,
            key_filename=ssh_key_filename,
            key_comment=ssh_key_comment,
            socket_path=gcr_ssh_agent_socket,
            enable_zsh=enable_zsh,
        )

    # Setup Java/Sdkman if enabled
    if enable_java:
        java.setup(user=user, home=home, tools=sdkman_tools, enable_zsh=enable_zsh)

    # Setup Flutter if enabled
    if enable_flutter:
        flutter.setup(user=user, home=home, enable_zsh=enable_zsh)

    # Remove ghostty if enabled
    if remove_ghostty:
        ghostty.remove(home=home)

    # Setup OpenVPN if enabled
    if enable_openvpn:
        openvpn.setup()

    # Setup Rambox if enabled
    if enable_rambox:
        rambox.setup()

    # Setup Zoom if enabled
    if enable_zoom:
        zoom.setup()

    # Setup Go if enabled
    if enable_go:
        go.setup(home=home, enable_zsh=enable_zsh)

    # Setup bat symlink if enabled
    if enable_bat:
        bat.setup(user=user, home=home)

    # Setup Python virtual environments if enabled
    if enable_python:
        python.setup(user=user, home=home, venvs=python_venvs, enable_zsh=enable_zsh)


if __name__ == "builtins":
    main()
