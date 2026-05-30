from pyinfra import host
from pyinfra.operations import files, server

# Get user from host data
user = host.data.get("user", "ubuntu")
homebrew_binaries_path = host.data.get("homebrew_binaries_path", "~/bin/brew")

if host.data.get("fzf", {}).get("enabled", False):
    # Install fzf package via homebrew
    server.shell(
        name="Install fzf package",
        commands=[f"{homebrew_binaries_path} install fzf"],
    )

    # Add fzf completion to bash
    files.block(
        name="Add fzf completion to bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: add fzf completion",
        content=f"""FZF_DEFAULT_OPTS="--tmux"
eval $({homebrew_binaries_path}/fzf --bash)""",
        try_prevent_shell_expansion=True,
    )

    # Add fzf completion to zsh if zsh is enabled
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Add fzf completion to zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} ANSIBLE MANAGED BLOCK: add fzf completion",
            content="""FZF_DEFAULT_OPTS="--tmux"
source <(fzf --zsh)""",
        )

    # Add aliases
    files.line(
        name="Add goto alias",
        path=f"/home/{user}/.bash_aliases",
        line="alias goto='cd $(find ~ -type d | fzf)'",
        replace="^alias goto=",
        present=True,
    )