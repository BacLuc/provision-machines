"""direnv setup."""

from pyinfra.operations import apt, files


def setup(user, home, enable_zsh):
    """Setup direnv package and shell integration."""
    apt.packages(
        name="Install direnv",
        packages=["direnv"],
        update=True,
    )

    files.block(
        name="Add direnv to bashrc",
        path=f"{home}/.bashrc",
        content='eval "$(direnv hook bash)"',
        marker="# {mark} ANSIBLE MANAGED BLOCK: source direnv",
    )

    if enable_zsh:
        files.block(
            name="Add direnv to zshrc",
            path=f"{home}/.zshrc",
            content='eval "$(direnv hook zsh)"',
            marker="# {mark} ANSIBLE MANAGED BLOCK: source direnv",
        )
