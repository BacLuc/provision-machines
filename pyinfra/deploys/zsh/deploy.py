from operations.filesystem import dirname_of
from pyinfra import host
from pyinfra.operations import apt, files, server
import io

user = host.data.get("user", "ubuntu")

if host.data.zsh["enabled"]:
    apt.packages(
        name="Install zsh",
        packages=["zsh"],
        _sudo=True,
    )

    server.shell(
        name="Setup initial zshrc",
        commands=[
            f'[ -f /home/{user}/.zshrc ] || cp {dirname_of(__file__)}/files/initial.zshrc /home/{user}/.zshrc'
        ],
    )

    apt.packages(
        name="Install fonts-powerline",
        packages=["fonts-powerline"],
        _sudo=True,
    )

    server.shell(
        name="Set zsh as default shell",
        commands=[f"chsh -s /bin/zsh {user}"],
        _sudo=True,
    )

    server.shell(
        name="Install oh-my-zsh",
        commands=[
            f'[ -d /home/{user}/.oh-my-zsh ] || sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
        ],
    )

    apt.packages(
        name="Install autojump",
        packages=["autojump"],
        _sudo=True,
    )

    apt.packages(
        name="Install zsh-syntax-highlighting",
        packages=["zsh-syntax-highlighting"],
        _sudo=True,
    )

    files.block(
        name="Autostart tmux in zsh",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: autostart tmux",
        content="""ZSH_TMUX_AUTOSTART=true
ZSH_TMUX_AUTOSTART_ONCE=false
ZSH_TMUX_AUTOCONNECT=false""",
        before=True,
        line="^plugins=",
    )

    for setting in [
        {"replace": "^ZSH_THEME=", "line": "ZSH_THEME=amuse"},
        {"replace": "^plugins=", "line": "plugins=(autojump azure git helm kubectx tmux)"},
    ]:
        files.line(
            name=f"Set zsh setting: {setting['line']}",
            path=f"/home/{user}/.zshrc",
            line=setting["line"],
            replace=setting["replace"],
        )

    files.block(
        name="Add lesspipe to zsh",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: zsh blocks taken from bash",
        content='[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"',
        try_prevent_shell_expansion=True,
    )

    if host.data.homebrew["enabled"]:
        homebrew_binaries_path = host.data.homebrew.get("binaries_path", "/home/linuxbrew/.linuxbrew/bin")
        files.block(
            name="Add homebrew to path in zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: homebrew",
            content=f'PATH="$PATH:{homebrew_binaries_path}"',
            try_prevent_shell_expansion=True,
        )

    files.block(
        name="Add zsh-syntax-highlighting",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add zsh-syntax-highlighting",
        content="source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh",
    )

    update_packages_dir = host.data.update_packages_script.get("dir")
    if update_packages_dir:
        files.put(
            name="Create oh-my-zsh upgrade script",
            src=io.StringIO(
                "#!/bin/sh\n"
                "\n"
                "set -e\n"
                "\n"
                f'user="{user}"\n'
                "\n"
                f'su "$user" -c "/home/{user}/.oh-my-zsh/tools/upgrade.sh"\n'
            ),
            dest=f"{update_packages_dir}/oh-my-zsh-upgrade",
            mode="755",
            _sudo=True,
        )

    completions_dir = f"/home/{user}/zsh/completions"

    files.directory(
        name="Create completions directory",
        path=completions_dir,
        mode="755",
        user=user,
        group=user,
    )

    server.shell(
        name="Install docker completion script",
        commands=[f"[ -f {completions_dir}/_docker ] || docker completion zsh > {completions_dir}/_docker"],
    )

    files.block(
        name="Source docker completion script",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add docker completion script",
        content=f"""source {completions_dir}/_docker

complete -F _docker dc""",
    )

    server.shell(
        name="Set zsh prompt theme",
        commands=[
            f"grep -q 'BEGIN PYINFRA MANAGED BLOCK: add zsh prompt theme' /home/{user}/.zshrc 2>/dev/null || "
            f"tee -a /home/{user}/.zshrc > /dev/null << 'ZSHPROMPT'\n"
            "# BEGIN PYINFRA MANAGED BLOCK: add zsh prompt theme\n"
            "PROMPT=\'%{$fg_bold[green]%}%~%{$reset_color%}$(git_prompt_info) %{$fg_bold[red]%}%*%{$reset_color%}\n$ \'\n"
            "# END PYINFRA MANAGED BLOCK: add zsh prompt theme\n"
            "ZSHPROMPT"
        ],
    )

    motd_path = "/etc/profile.d/update-motd.sh"
    files.block(
        name="Add motd banner to zsh",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add motd banner",
        content=f"""motd_path="{motd_path}"
test -f $motd_path && source $motd_path""",
        try_prevent_shell_expansion=True,
    )
