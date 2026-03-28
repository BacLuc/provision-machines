"""Lazygit installation and configuration."""

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.operations import server


@deploy("Install lazygit")
def setup(user=None, home=None, _sudo=None):
    """Install lazygit via homebrew."""
    # renovate: datasource=github-releases depName=jesseduffield/lazygit
    lazygit_version = "0.59.0"

    # Install lazygit via homebrew if available
    server.shell(
        name="Install lazygit via homebrew",
        commands=[f"~/bin/brew install lazygit"],
        _ignore_errors=True,
    )
