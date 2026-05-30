from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
)

# Get user from host data
user = host.data.get("user", "ubuntu")

# Set prettier image version
bash_prettier_image_version = "3.8.1"

# Install autojump
apt.packages(
    name="Install autojump",
    packages=["autojump"],
    _sudo=True,
)

# Add bash aliases
bash_aliases = [
    {"line": "alias ll='ls -lhA --color=auto'", "regexp": "^alias ll="},
    {"line": "alias cdp='cd $(pwd)'", "regexp": "^alias cdp="},
    {"line": "alias bigdirs='du --human-readable --max-depth=1 2> /dev/null | sort --human-numeric-sort -r | head -n20'", "regexp": "^alias bigdirs="},
    {"line": f"alias prettier='docker run --rm -v $PWD:/workdir -w /workdir -u $UID ghcr.io/bacluc/prettier-image/prettier-image:{bash_prettier_image_version}'", "regexp": "^alias prettier="},
]

for alias in bash_aliases:
    files.line(
        name=f"Add bash alias: {alias['line']}",
        path=f"/home/{user}/.bash_aliases",
        line=alias["line"],
        replace=alias["regexp"],
        present=True,
        _sudo=True,
    )

# Add bash exports
bash_exports = [
    {"line": "export HISTSIZE=9999", "regexp": "^export HISTSIZE="},
    {"line": "export HISTFILESIZE=99999", "regexp": "^export HISTFILESIZE="},
    {"line": "export LS_COLORS='di=0;35'", "regexp": "^export LS_COLORS="},
]

for export in bash_exports:
    files.line(
        name=f"Add bash export: {export['line']}",
        path=f"/home/{user}/.bashrc",
        line=export["line"],
        replace=export["regexp"],
        present=True,
        _sudo=True,
    )

# Add zsh exports if zsh is enabled
if host.data.get("zsh", {}).get("enabled", False):
    zsh_exports = [
        {"line": "export HISTSIZE=9999", "regexp": "^export HISTSIZE="},
        {"line": "export SAVEHIST=9999", "regexp": "^export SAVEHIST="},
        {"line": "DISABLE_MAGIC_FUNCTIONS=true", "regexp": "DISABLE_MAGIC_FUNCTIONS="},
    ]
    
    for export in zsh_exports:
        files.line(
            name=f"Add zsh export: {export['line']}",
            path=f"/home/{user}/.zshrc",
            line=export["line"],
            replace=export["regexp"],
            present=True,
            _sudo=True,
        )

# Source usual bash definitions
files.block(
    name="Source usual bash definitions",
    path=f"/home/{user}/.bashrc",
    marker="# {mark} ANSIBLE MANAGED BLOCK: usual bash definitions",
    content="""
# Source bash definitions
if [ -f /etc/bashrc ]; then
    source /etc/bashrc
fi
if [ -f ~/.bash_aliases ]; then
    source ~/.bash_aliases
fi
""",
    _sudo=True,
)

# Add snap bin to path in .bashrc
files.block(
    name="Add snap bin to path in .bashrc",
    path=f"/home/{user}/.bashrc",
    marker="# {mark} ANSIBLE MANAGED BLOCK: add snap bin to path",
    content="export PATH=\"/snap/bin:$PATH\"",
    _sudo=True,
    try_prevent_shell_expansion=True,
)

# Add snap bin to path in .zshrc if zsh is enabled
if host.data.get("zsh", {}).get("enabled", False):
    files.block(
        name="Add snap bin to path in .zshrc",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: add snap bin to path",
        content="export PATH=\"/snap/bin:$PATH\"",
        _sudo=True,
        try_prevent_shell_expansion=True,
    )

# Source autojump
files.block(
    name="Source autojump",
    path=f"/home/{user}/.bashrc",
    marker="# {mark} ANSIBLE MANAGED BLOCK: add autojump",
    content=". /usr/share/autojump/autojump.sh",
    _sudo=True,
)

# Source usual zsh definitions if zsh is enabled
if host.data.get("zsh", {}).get("enabled", False):
    files.block(
        name="Source usual zsh definitions",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: usual bash definitions",
        content="""
if [ -f ~/.bash_aliases ]; then
    source ~/.bash_aliases
fi
""",
        _sudo=True,
    )