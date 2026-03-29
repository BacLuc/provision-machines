"""direnv setup."""

from pyinfra.operations import apt, files


def setup(user, home, enable_zsh):
    """Setup direnv package and shell integration."""
    apt.packages(
        name="Install direnv",
        packages=["direnv"],
        update=True,
    )

    # Use files.line instead of files.block to avoid eval issues
    files.line(
        name="Add direnv to bashrc",
        path=f"{home}/.bashrc",
        line='eval "$(direnv hook bash)"',
        ensure_newline=True,
    )

    if enable_zsh:
        files.line(
            name="Add direnv to zshrc",
            path=f"{home}/.zshrc",
            line='eval "$(direnv hook zsh)"',
            ensure_newline=True,
        )
