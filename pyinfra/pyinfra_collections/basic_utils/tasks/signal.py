"""signal setup."""

from pyinfra.operations import server


def setup():
    """Setup Signal snap."""
    server.shell(
        name="Install Signal snap",
        commands=["snap install signal-desktop"],
        _ignore_errors=True,
    )
