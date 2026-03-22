"""Go setup."""

from pyinfra.operations import files, server


def setup(home, enable_zsh):
    """Setup Go via goenv."""
    # Install goenv via brew
    server.shell(
        name="Install goenv",
        commands=[f"{home}/bin/brew install goenv"],
    )

    files.block(
        name="Add goenv to bashrc",
        path=f"{home}/.bashrc",
        content="""export GOENV_ROOT="$HOME/.goenv"
eval "$(goenv init -)" """,
        marker="# {mark} ANSIBLE MANAGED BLOCK: add goenv",
    )

    if enable_zsh:
        files.block(
            name="Add goenv to zshrc",
            path=f"{home}/.zshrc",
            content="""export GOENV_ROOT="$HOME/.goenv"
export PATH="$GOENV_ROOT/bin:$PATH"
eval "$(goenv init -)" """,
            marker="# {mark} ANSIBLE MANAGED BLOCK: add goenv",
        )
