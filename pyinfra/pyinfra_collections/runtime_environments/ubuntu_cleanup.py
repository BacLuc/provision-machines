"""Ubuntu cleanup utilities."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Ubuntu Cleanup")
def configure_ubuntu_cleanup(user=None, home=None, _sudo=None):
    """Clean up Ubuntu system."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_ubuntu_cleanup", True)):
        return

    # Remove no more referenced packages
    apt.packages(
        name="Remove no more referenced packages",
        packages=[],
        present=False,
        auto_remove=True,
    )
