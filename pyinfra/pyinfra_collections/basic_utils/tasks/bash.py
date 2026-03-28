"""Bash configuration and aliases."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import files, apt


@deploy("Bash")
def configure_bash(user=None, home=None, enable_zsh=False, _sudo=None):
    """Configure bash with aliases and settings."""
    # Install autojump
    apt.packages(name="Install autojump", packages=["autojump"], update=True)

    # Add bash aliases
    aliases = [
        ("^alias ll=", "alias ll='ls -lhA --color=auto'"),
        ("^alias cdp=", "alias cdp='cd $(pwd)'"),
        ("^alias bigdirs=", "alias bigdirs='du -h --max-depth=1 | sort -hr | head -n 20'"),
    ]

    for pattern, line in aliases:
        files.line(
            path=f"{home}/.bash_aliases",
            line=line,
            regexp=pattern,
            ensure_newline=True,
        )

    # Add bash exports
    files.line(
        path=f"{home}/.bashrc",
        line="export HISTSIZE=9999",
        regexp="^export HISTSIZE=",
        ensure_newline=True,
    )
    files.line(
        path=f"{home}/.bashrc",
        line="export HISTFILESIZE=99999",
        regexp="^export HISTFILESIZE=",
        ensure_newline=True,
    )

    # Add snap bin to PATH
    files.block(
        path=f"{home}/.bashrc",
        content="export PATH=\"/snap/bin:$PATH\"",
        marker="# {mark} PYINFRA MANAGED: snap bin path",
    )

    # Source autojump
    files.block(
        path=f"{home}/.bashrc",
        content=". /usr/share/autojump/autojump.sh",
        marker="# {mark} PYINFRA MANAGED: autojump",
    )

    # Source bash_aliases if it exists
    files.block(
        path=f"{home}/.bashrc",
        content="if [ -f ~/.bash_aliases ]; then\n  source ~/.bash_aliases\nfi",
        marker="# {mark} PYINFRA MANAGED: source bash_aliases",
    )
