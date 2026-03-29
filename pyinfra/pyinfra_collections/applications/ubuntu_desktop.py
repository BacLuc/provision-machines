"""Ubuntu Desktop configuration."""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, server


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Ubuntu Desktop")
def configure_ubuntu_desktop(user=None, home=None, _sudo=None):
    """Configure Ubuntu desktop settings."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_ubuntu_desktop", True)):
        return

    # Install psutil for dconf module
    apt.packages(
        name="Install psutil",
        packages=["python3-psutil"],
    )

    # Install xfce-terminal
    apt.packages(
        name="Install xfce-terminal",
        packages=["xfce4-terminal"],
    )

    # Add German keyboard layouts
    server.shell(
        name="Add German keyboard layouts",
        commands=[
            'gsettings set org.gnome.desktop.input-sources sources "[(\"xkb\", \"ch\"), (\"xkb\", \"us\")]"'
        ],
        _ignore_errors=True,
    )

    # Configure workspace shortcuts
    shortcuts = [
        ("org.gnome.desktop.wm.keybindings", "switch-to-workspace-right", "'<Control><Super>Right'"),
        ("org.gnome.desktop.wm.keybindings", "switch-to-workspace-down", "'<Control><Super>Down'"),
        ("org.gnome.desktop.wm.keybindings", "switch-to-workspace-left", "'<Control><Super>Left'"),
        ("org.gnome.desktop.wm.keybindings", "switch-to-workspace-up", "'<Control><Super>Up'"),
        ("org.gnome.desktop.wm.keybindings", "maximize", "'<Super>Up'"),
        ("org.gnome.desktop.wm.keybindings", "unmaximize", "'<Super>Down'"),
    ]

    for schema, key, value in shortcuts:
        server.shell(
            name=f"Set {key} shortcut",
            commands=[f'gsettings set {schema} {key} {value}'],
            _ignore_errors=True,
        )
