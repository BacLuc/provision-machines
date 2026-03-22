"""Zsh shell setup and configuration."""

import os
from io import StringIO
from typing import Union

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, files, server





@deploy("Zsh")
def configure_zsh(
    user=None,
    home=None,
    enable_zsh_autosuggestions=True,
    enable_tmux_autostart=True,
    theme="amuse",
    motd_path: Union[str, bool] = "/etc/profile.d/update-motd.sh",
    completions_dir="~/zsh/completions",
    homebrew_path="",
    homebrew_home="",
    _sudo=None,
    **kwargs,
):
    """Setup Zsh shell with oh-my-zsh and plugins."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_zsh", False)):
        return

    # Get user/home from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    if home is None:
        home = f"/home/{user}"

    # Install zsh via apt
    apt.packages(
        name="Install zsh",
        packages=["zsh"],
        update=True,
    )

    # Install fonts-powerline for themes
    apt.packages(
        name="Install fonts-powerline",
        packages=["fonts-powerline"],
    )

    # Install autojump for better navigation
    apt.packages(
        name="Install autojump",
        packages=["autojump"],
    )

    # Install zsh-syntax-highlighting via apt
    apt.packages(
        name="Install zsh-syntax-highlighting",
        packages=["zsh-syntax-highlighting"],
    )

    # Check if .zshrc exists and create initial one if not
    zshrc_path = os.path.join(home, ".zshrc")
    if not os.path.exists(zshrc_path):
        files.put(
            name="Create initial .zshrc",
            src=StringIO("# .zshrc file managed by pyinfra\n"),
            dest=zshrc_path,
            mode="644",
        )

    # Set zsh as default shell if not already
    current_shell_result = server.shell(
        name="Get current shell",
        commands=["echo $SHELL"],
    )

    # current_shell_result may be a tuple, extract the shell string
    if isinstance(current_shell_result, tuple) and len(current_shell_result) > 0:
        current_shell = current_shell_result[0]
    else:
        current_shell = str(current_shell_result)

    if "/bin/zsh" not in current_shell and user:
        server.shell(
            name=f"Set default shell to zsh for {user}",
            commands=[f"chsh -s /bin/zsh {user}"],
        )

    # Check if oh-my-zsh is installed
    ohmyzsh_path = os.path.join(home, ".oh-my-zsh")
    if not os.path.exists(ohmyzsh_path):
        files.download(
            name="Download oh-my-zsh installer",
            src="https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh",
            dest="/tmp/oh-my-zsh-installer.sh",
            mode="755",
        )

        server.shell(
            name="Install oh-my-zsh",
            commands=["sh /tmp/oh-my-zsh-installer.sh --unattended"],
        )

    # Add tmux autostart configuration if enabled
    if enable_tmux_autostart:
        files.block(
            name="Add tmux autostart configuration to .zshrc",
            path=zshrc_path,
            content="""ZSH_TMUX_AUTOSTART=true
ZSH_TMUX_AUTOSTART_ONCE=false
ZSH_TMUX_AUTOCONNECT=false""",
            marker="# {mark} PYINFRA MANAGED BLOCK: autostart tmux",
        )

    # Set zsh theme
    files.line(
        name="Set ZSH theme in .zshrc",
        path=zshrc_path,
        line=f'ZSH_THEME="{theme}"',
        ensure_newline=True,
    )

    # Set plugins
    files.line(
        name="Set plugins in .zshrc",
        path=zshrc_path,
        line="plugins=(autojump azure git helm kubectx tmux)",
        ensure_newline=True,
    )

    # Add common bash blocks to zshrc
    files.block(
        name="Add common bash blocks to .zshrc",
        path=zshrc_path,
        content='[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"',
        marker="# {mark} PYINFRA MANAGED BLOCK: zsh blocks taken from bash",
        try_prevent_shell_expansion=True,
    )

    # Add homebrew to path if homebrew_path is specified
    if homebrew_path:
        files.block(
            name="Add homebrew to path in .zshrc",
            path=zshrc_path,
            content=f'PATH="$PATH:{homebrew_path}"',
            marker="# {mark} PYINFRA MANAGED BLOCK: homebrew",
        )

    # Add zsh-syntax-highlighting
    files.block(
        name="Add zsh-syntax-highlighting to .zshrc",
        path=zshrc_path,
        content="source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh",
        marker="# {mark} PYINFRA MANAGED BLOCK: add zsh-syntax-highlighting",
    )

    # Create completions directory
    expanded_completions_dir = os.path.expanduser(completions_dir)
    files.directory(
        name="Create zsh completions directory",
        path=expanded_completions_dir,
        mode="755",
    )

    # Add custom prompt theme
    files.block(
        name="Add custom zsh prompt theme",
        path=zshrc_path,
        content="""PROMPT='
%{$fg_bold[green]%}%~%{$reset_color%}$(git_prompt_info)$(virtualenv_prompt_info)$(azure_prompt_info) k:$(kubectx_prompt_info) ⌚ %{$fg_bold[red]%}%*%{$reset_color%}
$ '""",
        marker="# {mark} PYINFRA MANAGED BLOCK: add zsh prompt theme",
    )

    # Add MOTD banner if motd_path is not False
    if motd_path:
        files.block(
            name="Add MOTD banner to .zshrc",
            path=zshrc_path,
            content=f'motd_path="{motd_path}"\ntest -f $motd_path && source $motd_path',
            marker="# {mark} PYINFRA MANAGED BLOCK: add motd banner",
        )
