from pyinfra import host
from pyinfra.operations import apt, files, server

ubuntu_desktop_defaults = {
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
}

ubuntu_desktop = ubuntu_desktop_defaults.copy()
if host.data.get("ubuntu_desktop"):
    ubuntu_desktop.update(host.data.get("ubuntu_desktop", {}))

if host.data.get("enable_ubuntu_desktop", True):
    
    if ubuntu_desktop.get("enable_dependencies", True):
        apt.packages(
            name="Install psutil that is needed for dconf module below",
            packages=["python3-psutil"],
            _sudo=True,
        )
        
        apt.packages(
            name="Install xfce-terminal",
            packages=["xfce4-terminal"],
            _sudo=True,
        )
    
    if ubuntu_desktop.get("enable_favorite_apps", True):
        # Set favorite apps
        favorite_apps_list = [app["desktop_file_name"] for app in ubuntu_desktop["favorite_apps"]]
        favorite_apps_str = str(favorite_apps_list).replace("'", '"')
        
        server.shell(
            name="Define all gnome favorite apps",
            commands=[f"gsettings set /org/gnome/shell/favorite-apps '{favorite_apps_str}'"],
        )
        
        # Set keyboard shortcuts for favorite apps
        for index, app in enumerate(ubuntu_desktop["favorite_apps"]):
            server.shell(
                name=f"Set keyboard shortcut for {app['desktop_file_name']}",
                commands=[f"gsettings set org.gnome.shell.keybindings switch-to-application-{index + 1} '{app['shortcut']}'"],
            )
    
    if ubuntu_desktop.get("enable_keyboard_layouts", True):
        server.shell(
            name="Add german keyboard layouts",
            commands=["gsettings set /org/gnome/desktop/input-sources/sources '[('xkb', 'ch'), ('xkb', 'us')]'"],
        )
    
    if ubuntu_desktop.get("enable_shortcuts", True):
        gnome_shortcuts = [
            {
                "schema": "org.gnome.desktop.wm.keybindings",
                "key": "switch-to-workspace-right",
                "value": "['<Control><Super>Right']",
                "description": "add shortcut for switching workspace right",
            },
            {
                "schema": "org.gnome.desktop.wm.keybindings",
                "key": "switch-to-workspace-down",
                "value": "['<Control><Super>Down']",
                "description": "add shortcut for switching workspace down",
            },
            {
                "schema": "org.gnome.desktop.wm.keybindings",
                "key": "switch-to-workspace-left",
                "value": "['<Control><Super>Left']",
                "description": "add shortcut for switching workspace left",
            },
            {
                "schema": "org.gnome.desktop.wm.keybindings",
                "key": "switch-to-workspace-up",
                "value": "['<Control><Super>Up']",
                "description": "add shortcut for switching workspace up",
            },
        ]
        
        for shortcut in gnome_shortcuts:
            server.shell(
                name=f"Configure {shortcut['description']}",
                commands=[f"gsettings set {shortcut['schema']} {shortcut['key']} '{shortcut['value']}'"],
            )