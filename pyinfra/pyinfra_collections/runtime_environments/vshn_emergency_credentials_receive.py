"""VSHN Emergency Credentials Receive."""

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


@deploy("VSHN Emergency Credentials Receive")
def configure_vshn_emergency_credentials_receive(user=None, home=None, _sudo=None):
    """Install VSHN Emergency Credentials Receive tool."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_vshn_emergency_credentials_receive", False)):
        return

    # Get configuration
    version = host.data.get("emergency_credentials_receive_version", "1.2.2")
    checksum = host.data.get(
        "vshn_emergency_credentials_receive_checksum",
        "60eff914cb5e4b8771dd8606ba1b324e3183000c1a0fd91fa4ae2c82ad788afc",
    )

    home = home or os.path.expanduser("~")
    bin_dir = os.path.join(home, "bin")

    # Ensure ~/bin exists
    files.directory(
        name="Create ~/bin directory",
        path=bin_dir,
        present=True,
        mode="755",
    )

    # Download and install emergency-credentials-receive
    server.shell(
        name="Download and install emergency-credentials-receive",
        commands=[
            f"curl -fsSL https://github.com/vshn/emergency-credentials-receive/releases/download/v{version}/emergency-credentials-receive_linux_amd64 -o {bin_dir}/emergency-credentials-receive",
            f"chmod +x {bin_dir}/emergency-credentials-receive",
        ],
        _ignore_errors=True,
    )
