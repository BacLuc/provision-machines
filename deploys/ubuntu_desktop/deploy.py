from pyinfra import host
from pyinfra.operations import apt, server

ubuntu_desktop = host.data.ubuntu_desktop

if ubuntu_desktop["enabled"]:
    if ubuntu_desktop["enable_dependencies"]:
        apt.packages(
            name="Install psutil needed for dconf",
            packages=["python3-psutil"],
            _sudo=True,
        )

        apt.packages(
            name="Install xfce4-terminal",
            packages=["xfce4-terminal"],
            _sudo=True,
        )

    if ubuntu_desktop["enable_favorite_apps"]:
        favorite_apps = ubuntu_desktop["favorite_apps"]
        favorite_apps_value = "[" + ", ".join(f"'{app['desktop_file_name']}'" for app in favorite_apps) + "]"

        server.shell(
            name="Define all gnome favorite apps",
            commands=[f'dconf write /org/gnome/shell/favorite-apps "{favorite_apps_value}"'],
        )

        for index, app in enumerate(favorite_apps):
            server.shell(
                name=f"Set shortcut {app['shortcut']} for app {index + 1}",
                commands=[
                    f"gsettings set org.gnome.shell.keybindings switch-to-application-{index + 1} \"['{app['shortcut']}']\""
                ],
            )

    if ubuntu_desktop["enable_keyboard_layouts"]:
        server.shell(
            name="Add german keyboard layouts",
            commands=["dconf write /org/gnome/desktop/input-sources/sources \"[('xkb', 'ch'), ('xkb', 'us')]\""],
        )

    if ubuntu_desktop["enable_shortcuts"]:
        gnome_shortcuts = [
            ("org.gnome.desktop.wm.keybindings", "switch-to-workspace-right", "['<Control><Super>Right']"),
            ("org.gnome.desktop.wm.keybindings", "switch-to-workspace-down", "['<Control><Super>Down']"),
            ("org.gnome.desktop.wm.keybindings", "switch-to-workspace-left", "['<Control><Super>Left']"),
            ("org.gnome.desktop.wm.keybindings", "switch-to-workspace-up", "['<Control><Super>Up']"),
            ("org.gnome.desktop.wm.keybindings", "move-to-workspace-right", "['<Control><Shift><Alt>Right']"),
            ("org.gnome.desktop.wm.keybindings", "move-to-workspace-down", "['<Control><Shift><Alt>Down']"),
            ("org.gnome.desktop.wm.keybindings", "move-to-workspace-left", "['<Control><Shift><Alt>Left']"),
            ("org.gnome.desktop.wm.keybindings", "move-to-workspace-up", "['<Control><Shift><Alt>Up']"),
            ("org.gnome.mutter.keybindings", "toggle-tiled-right", "['<Super>Right']"),
            ("org.gnome.desktop.wm.keybindings", "unmaximize", "['<Super>Down']"),
            ("org.gnome.mutter.keybindings", "toggle-tiled-left", "['<Super>Left']"),
            ("org.gnome.desktop.wm.keybindings", "maximize", "['<Super>Up']"),
            ("org.gnome.desktop.wm.keybindings", "move-to-monitor-down", "['<Shift><Super>Down']"),
            ("org.gnome.desktop.wm.keybindings", "move-to-monitor-left", "['<Shift><Super>Left']"),
            ("org.gnome.desktop.wm.keybindings", "move-to-monitor-right", "['<Shift><Super>Right']"),
            ("org.gnome.desktop.wm.keybindings", "move-to-monitor-up", "['<Shift><Super>Up']"),
            ("org.gnome.mutter.keybindings", "switch-monitor", "[]"),
        ]

        for schema, key, value in gnome_shortcuts:
            server.shell(
                name=f"Set shortcut {schema} {key}",
                commands=[f'gsettings set {schema} {key} "{value}"'],
            )
