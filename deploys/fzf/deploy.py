import io

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import files, server

from operations.github_release_binary import github_release_binary
from operations.homebrew import HOMEBREW_BIN
from operations.user import get_user_name

user = get_user_name()
fzf = host.data.fzf
fzf_bin = f"/home/{user}/bin/fzf"

# renovate: datasource=github-releases depName=junegunn/fzf
fzf_version = "0.74.5"
fzf_checksum = "c8d3ac08594f271a108528beb15338c42be113d392816b10bf5955cd139293e8"

server.shell(
    name="Remove fzf installed by homebrew",
    commands=[f"rm -f {HOMEBREW_BIN}/fzf"],
    _sudo=True,
    _if=lambda: host.get_fact(File, f"{HOMEBREW_BIN}/fzf") is not None,
)

if fzf["enabled"]:
    github_release_binary(
        url=f"https://github.com/junegunn/fzf/releases/download/v{fzf_version}/fzf-{fzf_version}-linux_amd64.tar.gz",
        binary_name="fzf",
        checksum=fzf_checksum,
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
