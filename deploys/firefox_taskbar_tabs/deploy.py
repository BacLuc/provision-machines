import io
import json
import os
from urllib.parse import urlparse

from pyinfra import host
from pyinfra.facts.files import FileContents, FindFiles
from pyinfra.operations import files, server

from operations.filesystem import dirname_of
from operations.user import get_user_name

user = get_user_name()

firefox_taskbar_tabs = host.data.firefox_taskbar_tabs

taskbar_tabs = {
    "teams": (
        "Teams",
        "https://teams.microsoft.com/",
        "5b4e9bd5-8cd1-47ea-8945-66f73dd85fe8",
    ),
    "jira": (
        "Jira",
        "https://vshnticket.atlassian.net/",
        "05c3722e-4f98-4056-910b-d15d58628b22",
    ),
    "customer-service-board": (
        "CS Board",
        "https://vshnticket.atlassian.net/jira/software/c/projects/VSHNOPS/boards/95?quickFilter=660",
        "35699144-8592-4b92-8806-4a651d52b1f4",
    ),
    "confluence": (
        "Confluence",
        "https://vshnwiki.atlassian.net/",
        "40b8fc34-4f39-4a3a-927b-98eb493aed1a",
    ),
    "vshn-gitlab": (
        "VSHN GitLab",
        "https://git.vshn.net/",
        "44f1788e-8889-4097-8d8d-da60a1c68a06",
    ),
}

profiles_ini = """[General]
StartWithLastProfile=1
Version=2

[Profile0]
Name=default
IsRelative=1
Path=taskbar-tabs.default-release
Default=1
"""

if firefox_taskbar_tabs["enabled"]:
    icon_base = f"/home/{user}/.local/share/icons/hicolor"
    pixmaps_dir = f"/home/{user}/.local/share/pixmaps"
    applications_dir = f"/home/{user}/.local/share/applications"
    snap_profiles_root = f"/home/{user}/snap/firefox/common/.mozilla/firefox"
    deb_profiles_root = f"/home/{user}/.mozilla/firefox"

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

    profiles = host.get_fact(FindFiles, path=snap_profiles_root, fname="prefs.js", maxdepth=2) + host.get_fact(
        FindFiles, path=deb_profiles_root, fname="prefs.js", maxdepth=2
    )

    if not profiles:
        profile_dir = f"{snap_profiles_root}/taskbar-tabs.default-release"
        files.directory(
            name="Ensure directory " + profile_dir,
            path=profile_dir,
            user=user,
            group=user,
            mode="700",
        )
        files.file(
            name="Create empty Firefox prefs.js",
            path=f"{profile_dir}/prefs.js",
            user=user,
            group=user,
            mode="644",
            touch=True,
        )
        files.put(
            name="Create Firefox profiles.ini",
            src=io.StringIO(profiles_ini),
            dest=f"{snap_profiles_root}/profiles.ini",
            user=user,
            group=user,
            mode="644",
        )
        profiles = [f"{profile_dir}/prefs.js"]

    managed_ids = {entry[2] for entry in taskbar_tabs.values()}
    registry_entries: list[dict[str, object]] = []

    for key, (name, url, tab_id) in taskbar_tabs.items():
        icon_name = f"firefox-taskbar-tab-{key}"
        desktop_name = f"firefox_firefox.{key}.desktop"

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
Exec=firefox -taskbar-tab {tab_id} -new-window "{url}"
Icon={icon_name}
Terminal=false
Categories=Network;WebBrowser;
StartupNotify=true
StartupWMClass=firefox_firefox.{key}
"""
        files.put(
            name=f"Install {name} taskbar tab .desktop entry",
            src=io.StringIO(desktop_content),
            dest=f"{applications_dir}/{desktop_name}",
            user=user,
            group=user,
            mode="644",
        )

        files.file(
            name=f"Remove legacy {name} taskbar tab .desktop entry",
            path=f"{applications_dir}/firefox-taskbar-tab-{key}.desktop",
            present=False,
        )

        registry_entries.append(
            {
                "id": tab_id,
                "scopes": [{"hostname": urlparse(url).hostname}],
                "userContextId": 0,
                "startUrl": url,
                "name": name,
                "shortcutRelativePath": desktop_name,
            }
        )

    for prefs_js in profiles:
        registry_dir = f"{os.path.dirname(prefs_js)}/taskbartabs"
        registry_path = f"{registry_dir}/taskbartabs.json"

        existing = host.get_fact(FileContents, path=registry_path)
        kept: list[dict[str, object]] = []
        if existing:
            kept = [tab for tab in json.loads("\n".join(existing))["taskbarTabs"] if tab["id"] not in managed_ids]

        files.directory(
            name="Ensure directory " + registry_dir,
            path=registry_dir,
            user=user,
            group=user,
            mode="755",
        )
        files.put(
            name=f"Seed Firefox taskbar tabs registry in {registry_dir}",
            src=io.StringIO(json.dumps({"version": 1, "taskbarTabs": kept + registry_entries}, indent=2) + "\n"),
            dest=registry_path,
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
