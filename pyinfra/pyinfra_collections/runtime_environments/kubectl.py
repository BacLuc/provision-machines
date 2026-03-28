"""Kubectl and Kubernetes tools setup."""

import os

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, server, files


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)

@deploy("Kubectl")
def configure_kubectl(
    user=None,
    home=None,
    enable_zsh=False,
    _sudo=None,
    **kwargs,
):
    """Setup kubectl and related tools."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_kubectl", False)):
        return

    # Get user/home from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    if home is None:
        home = f"/home/{user}"

    # Install kubectl and helm via snap
    server.shell(
        name="Install kubectl and helm via snap",
        commands=["snap install kubectl --classic", "snap install helm --classic"],
        _ignore_errors=True,
    )

    # Install yq
    server.shell(
        name="Install yq",
        commands=["snap install yq"],
    )

    # Add kubectl completion for bash
    files.block(
        name="Add kubectl completion to bashrc",
        path=f"{home}/.bashrc",
        content="source <(kubectl completion bash)\ncomplete -F __start_kubectl k",
        marker="# {mark} PYINFRA MANAGED BLOCK: kubectl completion",
    )

    # Add kubectl aliases
    files.line(
        name="Add kubectl aliases",
        path=f"{home}/.bash_aliases",
        line="alias k=kubectl",
        ensure_newline=True,
    )

    # Install k9s
    server.shell(
        name="Install k9s",
        commands=["~/bin/brew install k9s"],
        _ignore_errors=True,
    )

    # Add k9s alias
    files.line(
        name="Add k9s alias",
        path=f"{home}/.bash_aliases",
        line="alias k9sa='k9s --as system:admin'",
        ensure_newline=True,
    )
