import io

from pyinfra import host
from pyinfra.operations import apt, files

from operations.user import get_user_name

user = get_user_name()

if host.data.alacritty["enabled"]:
    apt.packages(
        name="Install Alacritty",
        packages=["alacritty"],
        _sudo=True,
    )

    files.directory(
        name="Create Alacritty config directory",
        path=f"/home/{user}/.config/alacritty",
        user=user,
        group=user,
        mode="755",
    )

    files.download(
        name="Download Catppuccin Mocha theme",
        src="https://raw.githubusercontent.com/catppuccin/alacritty/f6cb5a5c2b404cdaceaff193b9c52317f62c62f7/catppuccin-mocha.toml",
        dest=f"/home/{user}/.config/alacritty/catppuccin-mocha.toml",
        user=user,
        group=user,
        mode="644",
    )

    font_size = host.data.alacritty["font_size"]
    default_shell = "/bin/zsh" if host.data.zsh["enabled"] else "/bin/bash"
    # noinspection PyRedeclaration
    default_shell = "/bin/zsh"

    alacritty_config = f"""import = [
    "~/.config/alacritty/catppuccin-mocha.toml"
]

[font]
size = {font_size}

[mouse]
hide_when_typing = false

[window]
decorations = "None"
startup_mode = "Maximized"

[shell]
program = "{default_shell}"
"""
    files.put(
        name="Provision Alacritty config",
        src=io.StringIO(alacritty_config),
        dest=f"/home/{user}/.config/alacritty/alacritty.toml",
        user=user,
        group=user,
        mode="644",
    )
