"""DevContainer CLI installation."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("DevContainer CLI")
def configure_devcontainer_cli(user=None, home=None, _sudo=None):
    """Install DevContainer CLI via npm."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_devcontainer_cli", False)):
        return

    # Install devcontainer CLI
    server.shell(
        name="Install devcontainer CLI",
        commands=["npm install -g @devcontainers/cli"],
        _ignore_errors=True,
    )
