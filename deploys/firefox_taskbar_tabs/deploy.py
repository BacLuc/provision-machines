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

taskbar_tabs = host.data.firefox_taskbar_tabs

if taskbar_tabs["enabled"]:
    taskbar_tabs = {key: tab for key, tab in taskbar_tabs["tabs"].items() if tab.get("enabled", True)}
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
        profiles = [f"{profile_dir}/prefs.js"]

    managed_desktops = {f"firefox_firefox.{key}.desktop" for key in taskbar_tabs}
    profile_signature = f'--profile "{snap_profiles_root}/taskbar-tabs.'
    own_orphans: set[str] = set()
    for desktop_path in host.get_fact(FindFiles, path=applications_dir, fname="firefox_firefox.*.desktop", maxdepth=1):
        desktop_name = os.path.basename(desktop_path)
        if desktop_name in managed_desktops:
            continue
        contents = host.get_fact(FileContents, path=desktop_path)
        if contents and profile_signature in "\n".join(contents):
            own_orphans.add(desktop_name)
            files.file(
                name="Remove removed taskbar tab " + desktop_name,
                path=desktop_path,
                present=False,
            )

    managed_ids = {tab["tab_id"] for tab in taskbar_tabs.values()}
    registry_entries: list[dict[str, object]] = []
    favorite_desktops: list[str] = []

    for key, tab in taskbar_tabs.items():
        name = tab["name"]
        url = tab["url"]
        tab_id = tab["tab_id"]
        icon_name = f"firefox-taskbar-tab-{key}"
        desktop_name = f"firefox_firefox.{key}.desktop"
        keyword_line = "Keywords={};\n".format(";".join([key, *tab.get("keywords", [])]))
        profile_dir = f"{snap_profiles_root}/taskbar-tabs.{key}"
        files.directory(
            name=f"Ensure {name} Firefox profile",
            path=profile_dir,
            user=user,
            group=user,
            mode="700",
        )
        files.put(
            name=f"Enable taskbar tabs in {name} Firefox profile",
            src=io.StringIO('user_pref("browser.taskbarTabs.enabled", true);\n'),
            dest=f"{profile_dir}/user.js",
            user=user,
            group=user,
            mode="644",
        )
        profile_prefs = f"{profile_dir}/prefs.js"
        if profile_prefs not in profiles:
            files.file(
                name=f"Create {name} Firefox prefs.js",
                path=profile_prefs,
                user=user,
                group=user,
                mode="644",
                touch=True,
            )
            profiles.append(profile_prefs)

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
{keyword_line}Exec=firefox --name=firefox_firefox.{key} --no-remote --profile "{profile_dir}" -taskbar-tab {tab_id} -new-window "{url}"
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
        favorite_desktops.append(desktop_name)

    url_prefixes = {prefix: key for key, tab in taskbar_tabs.items() for prefix in tab.get("url_prefixes", [])}
    handler_bin = f"/home/{user}/.local/bin"
    handler_script = f"{handler_bin}/vshn-taskbar-tab-url-handler"
    handler_desktop = "vshn-taskbar-tab-url-handler.desktop"
    if url_prefixes:
        url_prefix_tabs = json.dumps(
            [
                {
                    "prefix": prefix,
                    "key": key,
                    "tab_id": taskbar_tabs[key]["tab_id"],
                    "profile": f"{snap_profiles_root}/taskbar-tabs.{key}",
                }
                for key, tab in taskbar_tabs.items()
                for prefix in tab.get("url_prefixes", [])
            ],
            indent=2,
        )
        files.directory(
            name="Ensure directory " + handler_bin,
            path=handler_bin,
            user=user,
            group=user,
            mode="755",
        )
        files.put(
            name="Install taskbar tab url handler wrapper script",
            src=io.StringIO(
                f"""#!/usr/bin/env python3
import json
import subprocess
import sys
from urllib.parse import urlparse

url = sys.argv[1]
tabs = {url_prefix_tabs}

for tab in tabs:
    if not url.startswith(tab["prefix"]):
        continue
    profile_dir = tab["profile"]
    path = profile_dir + "/taskbartabs/taskbartabs.json"
    try:
        registry = json.load(open(path))
    except (OSError, ValueError):
        registry = None
    if isinstance(registry, dict):
        for entry in registry.get("taskbarTabs", []):
            if entry.get("id") == tab["tab_id"]:
                entry["startUrl"] = url
                entry["scopes"] = [{{"hostname": urlparse(url).hostname}}]
                with open(path, "w") as stream:
                    json.dump(registry, stream, indent=2)
    subprocess.run(
        [
            "firefox",
            "--name=firefox_firefox." + tab["key"],
            "--no-remote",
            "--profile",
            profile_dir,
            "-taskbar-tab",
            tab["tab_id"],
            "-new-window",
            url,
        ],
        check=False,
    )
    sys.exit()

subprocess.run(["firefox", url], check=False)
"""
            ),
            dest=handler_script,
            user=user,
            group=user,
            mode="755",
        )
        files.put(
            name="Install taskbar tab url handler .desktop entry",
            src=io.StringIO(
                f"""[Desktop Entry]
Version=1.0
Type=Application
Name=VSHN taskbar tabs URL handler
NoDisplay=true
Exec={handler_script} %u
Terminal=false
MimeType=x-scheme-handler/https;
StartupNotify=false
"""
            ),
            dest=f"{applications_dir}/{handler_desktop}",
            user=user,
            group=user,
            mode="644",
        )
        server.shell(
            name="Register https scheme handler",
            commands=[f"xdg-mime default {handler_desktop} x-scheme-handler/https 2>/dev/null || true"],
        )
    else:
        files.file(
            name="Remove taskbar tab url handler wrapper script",
            path=handler_script,
            present=False,
        )
        files.file(
            name="Remove taskbar tab url handler .desktop entry",
            path=f"{applications_dir}/{handler_desktop}",
            present=False,
        )
        # The https scheme registration is left in place. Remove it manually with
        # xdg-mime default firefox_firefox.desktop x-scheme-handler/https

    for prefs_js in profiles:
        registry_dir = f"{os.path.dirname(prefs_js)}/taskbartabs"
        registry_path = f"{registry_dir}/taskbartabs.json"

        existing = host.get_fact(FileContents, path=registry_path)
        kept: list[dict[str, object]] = []
        if existing:
            kept = [
                tab
                for tab in json.loads("\n".join(existing))["taskbarTabs"]
                if tab.get("id") not in managed_ids and tab.get("shortcutRelativePath") not in own_orphans
            ]

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
