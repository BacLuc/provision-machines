import io

from pyinfra import host
from pyinfra.operations import files, server

from operations.filesystem import dirname_of
from operations.user import get_user_name

user = get_user_name()

firefox_taskbar_tabs = host.data.firefox_taskbar_tabs

taskbar_tabs = {
    "teams": ("Teams", "https://teams.microsoft.com/"),
    "jira": ("Jira", "https://vshnticket.atlassian.net/"),
    "customer-service-board": (
        "CS Board",
        "https://vshnticket.atlassian.net/jira/software/c/projects/VSHNOPS/boards/95?quickFilter=660",
    ),
    "confluence": ("Confluence", "https://vshnwiki.atlassian.net/"),
    "vshn-gitlab": ("VSHN GitLab", "https://git.vshn.net/"),
}

if firefox_taskbar_tabs["enabled"]:
    icon_base = f"/home/{user}/.local/share/icons/hicolor"
    pixmaps_dir = f"/home/{user}/.local/share/pixmaps"
    applications_dir = f"/home/{user}/.local/share/applications"

    files.directory(
        name="Ensure directory " + applications_dir,
        path=applications_dir,
        user=user,
        group=user,
        mode="755",
    )
    files.directory(
        name="Ensure directory " + f"{icon_base}/256x256/apps",
        path=f"{icon_base}/256x256/apps",
        user=user,
        group=user,
        mode="755",
    )
    files.directory(
        name="Ensure directory " + pixmaps_dir,
        path=pixmaps_dir,
        user=user,
        group=user,
        mode="755",
    )

    for key, (name, url) in taskbar_tabs.items():
        icon_name = f"firefox-taskbar-tab-{key}"

        files.put(
            name=f"Install {name} icon to hicolor",
            src=f"{dirname_of(__file__)}/files/icons/{key}-256.png",
            dest=f"{icon_base}/256x256/apps/{icon_name}.png",
            user=user,
            group=user,
            mode="644",
        )

        files.put(
            name=f"Install {name} icon to pixmaps",
            src=f"{dirname_of(__file__)}/files/icons/{key}-256.png",
            dest=f"{pixmaps_dir}/{icon_name}.png",
            user=user,
            group=user,
            mode="644",
        )

        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={name}
Exec=firefox -taskbar-tab {key} -new-window "{url}"
Icon={icon_name}
Terminal=false
Categories=Network;WebBrowser;
StartupNotify=true
StartupWMClass={key}
"""
        files.put(
            name=f"Install {name} taskbar tab .desktop entry",
            src=io.StringIO(desktop_content),
            dest=f"{applications_dir}/firefox-taskbar-tab-{key}.desktop",
            user=user,
            group=user,
            mode="644",
        )

    server.shell(
        name="Refresh desktop database",
        commands=[
            f"update-desktop-database {applications_dir} 2>/dev/null || true",
            f"gtk-update-icon-cache -f -t {icon_base} >/dev/null 2>&1 || true",
        ],
    )
