"""Java/Sdkman setup."""

from pyinfra.context import host
from pyinfra.facts.files import Directory
from pyinfra.operations import files, server


def setup(user, home, tools, enable_zsh):
    """Setup Java via SDKMAN."""
    # Check if sdkman is installed
    sdkman_dir = host.get_fact(Directory, path=f"{home}/.sdkman")

    if not sdkman_dir:
        server.shell(
            name="Install SDKMAN",
            commands=["curl -s https://get.sdkman.io | bash"],
        )

    # Add sdkman to bashrc
    files.block(
        name="Add SDKMAN to bashrc",
        path=f"{home}/.bashrc",
        content=(
            """export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && """
            """source "$HOME/.sdkman/bin/sdkman-init.sh" """
        ),
        marker="# {mark} ANSIBLE MANAGED BLOCK: sdkman-init",
    )

    if enable_zsh:
        files.block(
            name="Add SDKMAN to zshrc",
            path=f"{home}/.zshrc",
            content=(
                """export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && """
                """source "$HOME/.sdkman/bin/sdkman-init.sh" """
            ),
            marker="# {mark} ANSIBLE MANAGED BLOCK: sdkman-init",
        )

    # Install tools
    for tool in tools:
        server.shell(
            name=f"Install {tool} via SDKMAN",
            commands=["bash -c 'source ~/.sdkman/bin/sdkman-init.sh; " f"sdk install {tool}'"],
        )
