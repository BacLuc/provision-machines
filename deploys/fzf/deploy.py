import io

from pyinfra import host
from pyinfra.operations import files

from operations.github_release_binary import github_release_binary
from operations.user import get_user_name

user = get_user_name()
fzf = host.data.fzf
fzf_bin = f"/home/{user}/bin/fzf"

if fzf["enabled"]:
    github_release_binary(
        url=f"https://github.com/junegunn/fzf/releases/download/v{fzf['fzf_version']}/fzf-{fzf['fzf_version']}-linux_amd64.tar.gz",
        binary_name="fzf",
        checksum=fzf["fzf_checksum"],
    )

    files.put(
        name="Add fzf completion for bash",
        src=io.StringIO(f"""\
FZF_DEFAULT_OPTS="--tmux"
eval $({fzf_bin} --bash)
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
source <({fzf_bin} --zsh)
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
