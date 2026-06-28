import io

from pyinfra.facts.files import Directory, File

from operations.filesystem import dirname_of
from operations.homebrew import HOMEBREW_BIN
from operations.user import get_user_name
from pyinfra import host
from pyinfra.operations import apt, files, server

user = get_user_name()

if host.data.zsh["enabled"]:
    completions_dir = host.data.zsh["completions_dir"].replace("{user}", user)
    motd_path = host.data.zsh["motd_path"]

    apt.packages(
        name="Install zsh, fonts-powerline and zsh-syntax-highlighting",
        packages=["zsh", "fonts-powerline", "zsh-syntax-highlighting", "autojump"],
        _sudo=True,
    )

    files.put(
        name="Setup initial zshrc",
        src=f"{dirname_of(__file__)}/files/initial.zshrc",
        dest=f"/home/{user}/.zshrc",
        user=user,
        group=user,
        mode="755",
        _if=lambda: host.get_fact(File, f"/home/{user}/.zshrc") is None,
    )

    server.user(
        name=f"Set default shell to zsh for {user}",
        user=user,
        shell="/bin/zsh",
        _sudo=True,
    )

    server.shell(
        name="Install oh-my-zsh",
        commands=[
            'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
        ],
        _if=lambda: host.get_fact(Directory, f"/home/{user}/.oh-my-zsh") is None,
    )

    files.block(
        name="Autostart tmux in zsh",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: autostart tmux",
        line="^plugins=",
        before=True,
        content="""ZSH_TMUX_AUTOSTART=true
ZSH_TMUX_AUTOSTART_ONCE=false
ZSH_TMUX_AUTOCONNECT=false""",
    )

    zshrc_lines = [
        {"line": "ZSH_THEME=amuse", "regexp": "^ZSH_THEME="},
        {"line": "plugins=(autojump azure git helm kubectx tmux)", "regexp": "^plugins="},
    ]

    for entry in zshrc_lines:
        files.line(
            name=f"Add zshrc line: {entry['line']}",
            path=f"/home/{user}/.zshrc",
            line=entry["regexp"],
            replace=entry["line"],
            present=True,
        )

    files.put(
        name="Add lesspipe script",
        src=io.StringIO('[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"\n'),
        dest=f"/home/{user}/.zshrc.d/lesspipe.zsh",
        user=user,
        group=user,
        mode="644",
    )

    files.put(
        name="Add homebrew to path in zsh",
        src=io.StringIO(f'PATH="$PATH:{HOMEBREW_BIN}"\n'),
        dest=f"/home/{user}/.zshrc.d/homebrew-path.zsh",
        user=user,
        group=user,
        mode="644",
    )

    files.block(
        name="Add zsh-syntax-highlighting to zshrc",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: add zsh-syntax-highlighting",
        content="source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh",
    )

    oh_my_zsh_upgrade = f"""#/bin/sh

set -e

user="{user}"

su "$user" -c "/home/{user}/.oh-my-zsh/tools/upgrade.sh"
"""
    files.put(
        name="Add oh-my-zsh upgrade script",
        src=io.StringIO(oh_my_zsh_upgrade),
        dest=f"{host.data.update_packages_script['dir']}/oh-my-zsh-upgrade",
        _sudo=True,
        mode="755",
    )

    files.directory(
        name="Create completions dir",
        path=completions_dir,
        user=user,
        group=user,
        mode="755",
    )

    server.shell(
        name="Install docker completion script",
        commands=[f"docker completion zsh > {completions_dir}/_docker"],
        _if=lambda: host.get_fact(File, f"{completions_dir}/_docker") is None,
    )

    files.block(
        name="Source docker completion script in zsh",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: add docker completion script",
        content=f"""source {completions_dir}/_docker

complete -F _docker dc""",
    )

    files.put(
        name="Add zsh prompt theme",
        src=io.StringIO(
            """PROMPT='
%{$fg_bold[green]%}%~%{$reset_color%}$(git_prompt_info)$(virtualenv_prompt_info)$(azure_prompt_info) k:$(kubectx_prompt_info) ⌚ %{$fg_bold[red]%}%*%{$reset_color%}
$ '
"""
        ),
        dest=f"/home/{user}/.zshrc.d/prompt.zsh",
        user=user,
        group=user,
        mode="644",
    )

    files.block(
        name="Add motd banner to zsh",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: add motd banner",
        content=f"test -f {motd_path} && source {motd_path}",
    )
