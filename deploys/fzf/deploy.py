import io

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import files, server

from operations.homebrew import HOMEBREW_BIN, user_brew_bin
from operations.user import get_user_name

user = get_user_name()

if host.data.fzf["enabled"]:
    if host.get_fact(File, f"{HOMEBREW_BIN}/fzf") is None:
        server.shell(
            name="Install fzf via brew",
            commands=[user_brew_bin(user) + " install fzf"],
        )

    files.put(
        name="Add fzf completion for bash",
        src=io.StringIO(f"""\
FZF_DEFAULT_OPTS="--tmux"
eval $({HOMEBREW_BIN}/fzf --bash)
"""),
        dest=f"/home/{user}/.bashrc.d/fzf-completion.sh",
        user=user,
        group=user,
        mode="644",
    )

    if host.data.zsh["enabled"]:
        files.put(
            name="Add fzf completion for zsh",
            src=io.StringIO(f"""\
FZF_DEFAULT_OPTS="--tmux"
source <({HOMEBREW_BIN}/fzf --zsh)
"""),
            dest=f"/home/{user}/.zshrc.d/fzf-completion.zsh",
            user=user,
            group=user,
            mode="644",
        )

    files.line(
        name="Add goto alias",
        path=f"/home/{user}/.bash_aliases",
        line="^alias goto=",
        replace="alias goto='cd $(find ~ -type d | fzf)'",
        present=True,
    )
