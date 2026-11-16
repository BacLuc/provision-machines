import io
import os

from pyinfra import host
from pyinfra.facts.files import FileContents, FindFiles
from pyinfra.operations import files, server

from operations.user import get_user_name

user = get_user_name()

desktop_url_files = host.data.desktop_url_files

if desktop_url_files["enabled"]:
    applications_dir = f"/home/{user}/.local/share/applications"
    marker = "X-Desktop-Url-File=true"

    files.directory(
        name="Ensure directory " + applications_dir,
        path=applications_dir,
        user=user,
        group=user,
        mode="755",
    )

    managed_desktops = {f"{key}.desktop" for key in desktop_url_files["files"]}

    for desktop_path in host.get_fact(FindFiles, path=applications_dir, fname="*.desktop", maxdepth=1):
        desktop_name = os.path.basename(desktop_path)
        if desktop_name in managed_desktops:
            continue
        contents = host.get_fact(FileContents, path=desktop_path)
        if contents and marker in "\n".join(contents):
            files.file(
                name="Remove removed url desktop file " + desktop_name,
                path=desktop_path,
                present=False,
            )

    for key, entry in desktop_url_files["files"].items():
        desktop_name = f"{key}.desktop"
        icon_line = f"Icon={entry['icon']}\n" if entry.get("icon") else ""
        schemes = entry.get("schemes", [])
        mime_type_line = ""
        no_display_line = ""
        if schemes:
            mime_type_line = "MimeType={};\n".format(";".join(f"x-scheme-handler/{scheme}" for scheme in schemes))
            no_display_line = "NoDisplay=true\n"

        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={entry["name"]}
Exec=xdg-open "{entry["url"]}"
{icon_line}{mime_type_line}{no_display_line}Terminal=false
Categories=Network;
StartupNotify=true
{marker}
"""
        files.put(
            name=f"Install {entry['name']} url desktop file",
            src=io.StringIO(desktop_content),
            dest=f"{applications_dir}/{desktop_name}",
            user=user,
            group=user,
            mode="644",
        )

        for scheme in schemes:
            server.shell(
                name=f"Register {entry['name']} handler for {scheme}",
                commands=[f"xdg-mime default {desktop_name} x-scheme-handler/{scheme} 2>/dev/null || true"],
            )

    server.shell(
        name="Refresh desktop database",
        commands=[f"update-desktop-database {applications_dir} 2>/dev/null || true"],
    )
