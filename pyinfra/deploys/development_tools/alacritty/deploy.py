import io

from pyinfra import host
from pyinfra.operations import apt, files

user = host.data.get("user", "ubuntu")

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

    font_size = host.data.alacritty.get("font_size", 12)

    alacritty_config = (
        "import = [\n"
        "    \"~/.config/alacritty/catppuccin-mocha.toml\"\n"
        "]\n"
        "\n"
        "[font]\n"
        f"size = {font_size}\n"
        "\n"
        "[mouse]\n"
        "hide_when_typing = false\n"
        "\n"
        "[window]\n"
        "startup_mode = \"Maximized\"\n"
    )
    files.put(
        name="Provision Alacritty config",
        src=io.StringIO(alacritty_config),
        dest=f"/home/{user}/.config/alacritty/alacritty.toml",
        user=user,
        group=user,
        mode="644",
    )
