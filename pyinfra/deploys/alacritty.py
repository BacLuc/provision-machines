from pyinfra import host
from pyinfra.operations import apt, files, server

user = host.data.get("user", "ubuntu")

alacritty_defaults = {
    "font_size": 12,
}

alacritty = alacritty_defaults.copy()
if host.data.get("alacritty"):
    alacritty.update(host.data.get("alacritty", {}))

if host.data.get("enable_alacritty", False):
    
    apt.packages(
        name="Install alacritty",
        packages=["alacritty"],
        _sudo=True,
    )
    
    files.directory(
        name="Create Alacritty config directory",
        path=f"/home/{user}/.config/alacritty",
        mode="755",
    )
    
    files.download(
        name="Download Catppuccin Mocha theme",
        src="https://raw.githubusercontent.com/catppuccin/alacritty/f6cb5a5c2b404cdaceaff193b9c52317f62c62f7/catppuccin-mocha.toml",
        dest=f"/home/{user}/.config/alacritty/catppuccin-mocha.toml",
        mode="644",
    )
    
    files.put(
        name="Provision Alacritty config",
        dest=f"/home/{user}/.config/alacritty/alacritty.toml",
        content=f"""import = [
    "~/.config/alacritty/catppuccin-mocha.toml"
]

[font]
size = {alacritty['font_size']}

[mouse]
hide_when_typing = false

[window]
startup_mode = "Maximized"
""",
        mode="644",
    )