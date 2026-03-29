"""VSHN tools installation."""

import os

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server, files


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("VSHN Tools")
def configure_vshn_tools(user=None, home=None, _sudo=None):
    """Install VSHN tools (appcat-cli, k8ify)."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_vshn_tools", False)):
        return

    home = home or os.path.expanduser("~")
    bin_dir = os.path.join(home, "bin")

    # Get configuration
    appcat_cli_version = host.data.get("appcat_cli_version", "0.5.0")
    appcat_cli_checksum = host.data.get(
        "appcat_cli_checksum",
        "2141bf312b56ff7baf7727a98bbe0488dab7769162fb88e63255209e3e8140f1",
    )
    k8ify_version = host.data.get("k8ify_version", "2.5.0")
    k8ify_checksum = host.data.get(
        "k8ify_checksum",
        "f3605d34439c0bef36930c71ad2b066acc0ba821e68c98e764fffc1a66dcc3b9",
    )

    # Ensure ~/bin exists
    files.directory(
        name="Create ~/bin directory",
        path=bin_dir,
        present=True,
        mode="755",
    )

    # Install appcat-cli
    server.shell(
        name="Download and install appcat-cli",
        commands=[
            f"curl -fsSL https://github.com/vshn/appcat-cli/releases/download/v{appcat_cli_version}/appcat-cli_{appcat_cli_version}_linux_amd64.tar.gz -o /tmp/appcat-cli.tar.gz",
            f"tar -xzf /tmp/appcat-cli.tar.gz -C {bin_dir}",
            f"rm /tmp/appcat-cli.tar.gz",
        ],
        _ignore_errors=True,
    )

    # Install k8ify
    server.shell(
        name="Download and install k8ify",
        commands=[
            f"curl -fsSL https://github.com/vshn/k8ify/releases/download/v{k8ify_version}/k8ify_{k8ify_version}_linux_amd64.tar.gz -o /tmp/k8ify.tar.gz",
            f"tar -xzf /tmp/k8ify.tar.gz -C {bin_dir}",
            f"rm /tmp/k8ify.tar.gz",
        ],
        _ignore_errors=True,
    )

    # Add commodore alias
    files.line(
        name="Add commodore alias",
        path=f"{home}/.bash_aliases",
        line="alias commodore='docker run --rm --user=\"${UID}\" --volume \"${PWD}:/app/data\" --workdir /app/data projectsyn/commodore:${COMMODORE_VERSION:=v1.29.0}'",
        ensure_newline=True,
    )
