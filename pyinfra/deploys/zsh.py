from pyinfra import host
from pyinfra.operations import apt, files, server, user
from pyinfra.facts.files import File
from pyinfra.facts.server import User, Shell


def zsh():
    zsh_config = host.data.get("zsh", {})
    
    if not zsh_config.get("enabled", False):
        return

    zsh_defaults = {
        "completions_dir": "~/zsh/completions",
        "motd_path": "/etc/profile.d/update-motd.sh",
    }
    
    zsh_config = {**zsh_defaults, **zsh_config}

    apt.packages(
        name="Install zsh",
        packages=["zsh"],
        _sudo=True,
    )

    zshrc_exists = host.get_fact(File, path="~/.zshrc")
    
    if not zshrc_exists:
        files.put(
            name="Setup initial zshrc",
            src="files/zsh/initial.zshrc",
            dest="~/.zshrc",
            mode="755",
        )

    apt.packages(
        name="Install fonts-powerline",
        packages=["fonts-powerline"],
        _sudo=True,
    )

    current_shell = host.get_fact(Shell)
    user_name = host.get_fact(User)
    
    if current_shell != "/bin/zsh":
        user.user(
            name="Set zsh as default shell",
            user=user_name,
            shell="/bin/zsh",
            _sudo=True,
        )

    ohmyzsh_exists = host.get_fact(File, path="~/.oh-my-zsh")
    
    if not ohmyzsh_exists:
        server.shell(
            name="Install oh-my-zsh",
            commands=[
                'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
            ],
        )

    apt.packages(
        name="Install autojump",
        packages=["autojump"],
        _sudo=True,
    )

    if zsh_config.get("enable_zsh_autosuggestions", False):
        server.shell(
            name="Install zsh-autosuggestions",
            commands=["~/bin/brew install zsh-autosuggestions"],
        )

    apt.packages(
        name="Install zsh-syntax-highlighting",
        packages=["zsh-syntax-highlighting"],
        _sudo=True,
    )

    files.block(
        name="Autostart tmux in zsh",
        path="~/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: autostart tmux",
        insert_before="^plugins=",
        block="""
ZSH_TMUX_AUTOSTART=true
ZSH_TMUX_AUTOSTART_ONCE=false
ZSH_TMUX_AUTOCONNECT=false
        """.strip(),
    )

    zsh_settings = [
        {"regex": "^ZSH_THEME=", "line": "ZSH_THEME=amuse"},
        {"regex": "^plugins=", "line": "plugins=(autojump azure git helm kubectx tmux)"},
    ]

    for setting in zsh_settings:
        files.line(
            name=f"Set zsh setting: {setting['line']}",
            path="~/.zshrc",
            line=setting["line"],
            regex=setting["regex"],
        )

    files.block(
        name="Add some blocks to .zshrc",
        path="~/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: zsh blocks taken from bash",
        block="[ -x /usr/bin/lesspipe ] && eval \"$(SHELL=/bin/sh lesspipe)\"",
    )

    homebrew_config = host.data.get("homebrew", {})
    if homebrew_config.get("enabled", False):
        files.block(
            name="Add homebrew to path",
            path="~/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: homebrew",
            block=f'PATH="$PATH:{homebrew_config.get("binaries_path", "/home/linuxbrew/.linuxbrew/bin")}"',
        )

    if zsh_config.get("enable_zsh_autosuggestions", False):
        zsh_autosuggestions_exists = host.get_fact(
            File, 
            path=f"{homebrew_config.get('home', '/home/linuxbrew/.linuxbrew')}/Homebrew/Cellar/zsh-autosuggestions"
        )
        
        if zsh_autosuggestions_exists:
            files.block(
                name="Add zsh-autosuggestions",
                path="~/.zshrc",
                marker="# {mark} PYINFRA MANAGED BLOCK: add zsh-autosuggestions",
                block="source $(~/bin/brew --prefix)/Homebrew/Cellar/zsh-autosuggestions",
            )

    files.block(
        name="Add zsh-syntax-highlighting",
        path="~/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add zsh-syntax-highlighting",
        block="source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh",
    )

    update_packages_config = host.data.get("update_packages_script", {})
    if update_packages_config.get("dir"):
        files.template(
            name="Create oh-my-zsh upgrade script",
            src="templates/zsh/oh-my-zsh-upgrade.j2.sh",
            dest=f"{update_packages_config['dir']}/oh-my-zsh-upgrade",
            mode="755",
            _sudo=True,
        )

    files.directory(
        name="Create completions directory",
        path=zsh_config["completions_dir"],
        mode="755",
    )

    docker_completion_exists = host.get_fact(File, path=f"{zsh_config['completions_dir']}/_docker")
    
    if not docker_completion_exists:
        server.shell(
            name="Install docker completion script",
            commands=[f"docker completion zsh > {zsh_config['completions_dir']}/_docker"],
        )

    files.block(
        name="Source docker completion script",
        path="~/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add docker completion script",
        block=f"""
source {zsh_config['completions_dir']}/_docker

complete -F _docker dc
        """.strip(),
    )

    files.block(
        name="Set zsh prompt theme",
        path="~/.zshrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add zsh prompt theme",
        block="""
PROMPT='
%{$fg_bold[green]%}%~%{$reset_color%}$(git_prompt_info)$(virtualenv_prompt_info)$(azure_prompt_info) k:$(kubectx_prompt_info) ⌚ %{$fg_bold[red]%}%*%{$reset_color%}
$ '
        """.strip(),
    )

    if zsh_config.get("motd_path"):
        files.block(
            name="Add motd banner",
            path="~/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: add motd banner",
            block=f"""
motd_path="{zsh_config['motd_path']}"
test -f $motd_path && source $motd_path
            """.strip(),
        )