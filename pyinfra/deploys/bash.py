from pyinfra import host
from pyinfra.operations import apt, files, server


def bash():

    apt.packages(
        name="Install autojump",
        packages=["autojump"],
        _sudo=True,
    )

    bash_aliases = [
        {"regex": "^alias ll=", "line": "alias ll='ls -lhA --color=auto'"},
        {"regex": "^alias cdp=", "line": "alias cdp='cd $(pwd)'"},
        {
            "regex": "^alias bigdirs=",
            "line": "alias bigdirs='du --human-readable --max-depth=1 2> /dev/null | sort --human-numeric-sort -r | head -n20'",
        },
        {
            "regex": "^alias prettier=",
            "line": "alias prettier='docker run --rm -v $PWD:/workdir -w /workdir -u $UID ghcr.io/bacluc/prettier-image/prettier-image:3.8.1'",
        },
    ]

    for alias in bash_aliases:
        files.line(
            name=f"Add bash alias: {alias['line']}",
            path="~/.bash_aliases",
            line=alias["line"],
            regex=alias["regex"],
        )

    bash_exports = [
        {"regex": "^export HISTSIZE=", "line": "export HISTSIZE=9999"},
        {"regex": "^export HISTFILESIZE=", "line": "export HISTFILESIZE=99999"},
        {"regex": "^export LS_COLORS=", "line": "export LS_COLORS='di=0;35'"},
    ]

    for export in bash_exports:
        files.line(
            name=f"Add bash export: {export['line']}",
            path="~/.bashrc",
            line=export["line"],
            regex=export["regex"],
        )

    if host.data.get("zsh", {}).get("enabled", False):
        zsh_exports = [
            {"regex": "^export HISTSIZE=", "line": "export HISTSIZE=9999"},
            {"regex": "^export SAVEHIST=", "line": "export SAVEHIST=9999"},
            {"regex": "DISABLE_MAGIC_FUNCTIONS=", "line": "DISABLE_MAGIC_FUNCTIONS=true"},
        ]

        for export in zsh_exports:
            files.line(
                name=f"Add zsh export: {export['line']}",
                path="~/.zshrc",
                line=export["line"],
                regex=export["regex"],
            )

    files.block(
        name="Source usual bash definitions",
        path="~/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: usual bash definitions",
        block="""
# Source bash definitions
if [ -f /etc/bashrc ]; then
    source /etc/bashrc
fi
if [ -f ~/.bash_aliases ]; then
    source ~/.bash_aliases
fi
        """.strip(),
    )

    files.block(
        name="Add snap bin to path in .bashrc",
        path="~/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add snap bin to path",
        block='export PATH="/snap/bin:$PATH"',
    )

    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Add snap bin to path in .zshrc",
            path="~/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: add snap bin to path",
            block='export PATH="/snap/bin:$PATH"',
        )

    files.block(
        name="Source autojump",
        path="~/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add autojump",
        block=". /usr/share/autojump/autojump.sh",
    )

    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Source usual zsh definitions",
            path="~/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: usual bash definitions",
            block="""
if [ -f ~/.bash_aliases ]; then
    source ~/.bash_aliases
fi
            """.strip(),
        )