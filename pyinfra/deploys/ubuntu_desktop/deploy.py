from pyinfra import host
from pyinfra.operations import apt, server

ubuntu_desktop = {
    "enable_dependencies": True,
    "enable_favorite_apps": True,
    "enable_keyboard_layouts": True,
    "enable_shortcuts": True,
    "enable_gpaste_config": False,
    "enable_testing_browser_desktop": False,
    "favorite_apps": [
        {"desktop_file_name": "Alacritty.desktop", "shortcut": "<Super>z"},
        {"desktop_file_name": "firefox_firefox.desktop", "shortcut": "<Super>u"},
        {"desktop_file_name": "phpstorm_phpstorm.desktop", "shortcut": "<Super>i"},
        {"desktop_file_name": "dev.zed.Zed.desktop", "shortcut": "<Super>o"},
        {"desktop_file_name": "gitclient.desktop", "shortcut": "<Super>g"},
    ],
    **host.data.ubuntu_desktop,
}

if host.data.ubuntu_desktop["enabled"]:
    if ubuntu_desktop["enable_dependencies"]:
        apt.packages(
            name="Install psutil for dconf module",
            packages=["python3-psutil"],
            _sudo=True,
        )

        apt.packages(
            name="Install xfce-terminal",
            packages=["xfce4-terminal"],
            _sudo=True,
        )

    if ubuntu_desktop["enable_favorite_apps"]:
        apps = [app["desktop_file_name"] for app in ubuntu_desktop["favorite_apps"]]
        apps_value = "['" + "','".join(apps) + "']"

        server.shell(
            name="Define gnome favorite apps",
            commands=[f"gsettings set org.gnome.shell favorite-apps \"{apps_value}\" || true"],
        )

        for index, app in enumerate(ubuntu_desktop["favorite_apps"]):
            server.shell(
                name=f"Set keyboard shortcut for {app['desktop_file_name']}",
                commands=[f"gsettings set org.gnome.shell.keybindings switch-to-application-{index + 1} \"['{app['shortcut']}']\" || true"],
            )

    if ubuntu_desktop["enable_keyboard_layouts"]:
        server.shell(
            name="Add keyboard layouts",
            commands=["gsettings set org.gnome.desktop.input-sources sources \"[(\'xkb\', \'ch\'), (\'xkb\', \'us\')]\" || true"],
        )

    if ubuntu_desktop["enable_shortcuts"]:
        for shortcut in [
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "switch-to-workspace-right", "value": "[\'<Control><Super>Right\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "switch-to-workspace-down", "value": "[\'<Control><Super>Down\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "switch-to-workspace-left", "value": "[\'<Control><Super>Left\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "switch-to-workspace-up", "value": "[\'<Control><Super>Up\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "move-to-workspace-right", "value": "[\'<Control><Shift><Alt>Right\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "move-to-workspace-down", "value": "[\'<Control><Shift><Alt>Down\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "move-to-workspace-left", "value": "[\'<Control><Shift><Alt>Left\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "move-to-workspace-up", "value": "[\'<Control><Shift><Alt>Up\']"},
            {"schema": "org.gnome.mutter.keybindings", "key": "toggle-tiled-right", "value": "[\'<Super>Right\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "unmaximize", "value": "[\'<Super>Down\']"},
            {"schema": "org.gnome.mutter.keybindings", "key": "toggle-tiled-left", "value": "[\'<Super>Left\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "maximize", "value": "[\'<Super>Up\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "move-to-monitor-down", "value": "[\'<Shift><Super>Down\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "move-to-monitor-left", "value": "[\'<Shift><Super>Left\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "move-to-monitor-right", "value": "[\'<Shift><Super>Right\']"},
            {"schema": "org.gnome.desktop.wm.keybindings", "key": "move-to-monitor-up", "value": "[\'<Shift><Super>Up\']"},
            {"schema": "org.gnome.mutter.keybindings", "key": "switch-monitor", "value": "[]"},
        ]:
            server.shell(
                name=f"Configure shortcut {shortcut['key']}",
                commands=[f"gsettings set {shortcut['schema']} {shortcut['key']} \"{shortcut['value']}\" || true"],
            )
