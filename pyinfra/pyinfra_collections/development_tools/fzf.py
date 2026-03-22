"""Fzf fuzzy finder setup and configuration."""

import os

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, files, server


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Fzf")
def configure_fzf(
    user=None,
    home=None,
    homebrew_path="",
    homebrew_home="",
    enable_zsh=False,
    fzf_default_opts="--tmux",
    _sudo=None,
    **kwargs,
):
    """Setup Fzf fuzzy finder with shell integration."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_fzf", False)):
        return

    # Get user/home from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    if home is None:
        home = f"/home/{user}"

    # Get config from host.data
    fzf_config = host.data.get("fzf", {})
    if not fzf_default_opts:
        fzf_default_opts = fzf_config.get("fzf_default_opts", "--tmux")

    # Check if zsh is enabled
    if not enable_zsh:
        enable_zsh = _parse_bool(host.data.get("enable_zsh", False))

    # Install fzf via homebrew if paths are provided
    if homebrew_home:
        fzf_bin = f"{homebrew_home}/.linuxbrew/bin/fzf"
        server.shell(
            name="Install fzf via homebrew",
            commands=["~/bin/brew install fzf"],
        )
    elif homebrew_path:
        fzf_bin = f"{homebrew_path}/fzf"
    else:
        # Fallback: install via apt
        apt.packages(
            name="Install fzf via apt",
            packages=["fzf"],
            update=True,
        )
        fzf_bin = "/usr/bin/fzf"

    # Add fzf completion to bash
    bashrc_content = f"""
FZF_DEFAULT_OPTS="{fzf_default_opts}"
eval $({fzf_bin} --bash)
"""

    files.block(
        name="Add fzf completion to bash",
        path=f"{home}/.bashrc",
        content=bashrc_content,
        marker="# {mark} ANSIBLE MANAGED BLOCK: add fzf completion",
    )

    # Add fzf completion to zsh if enabled
    if enable_zsh:
        zshrc_content = f"""
FZF_DEFAULT_OPTS="{fzf_default_opts}"
source <(fzf --zsh)
"""

        files.block(
            name="Add fzf completion to zsh",
            path=f"{home}/.zshrc",
            content=zshrc_content,
            marker="# {mark} ANSIBLE MANAGED BLOCK: add fzf completion",
        )

    # Add aliases
    files.line(
        name="Add goto alias",
        path=f"{home}/.bash_aliases",
        line="alias goto='cd $(find ~ -type d | fzf)'",
        ensure_newline=True,
    )
