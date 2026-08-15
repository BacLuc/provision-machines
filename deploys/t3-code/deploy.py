import io

from pyinfra import host
from pyinfra.operations import files, server

from operations.filesystem import dirname_of
from operations.user import get_user_name

user = get_user_name()

t3_code = host.data.t3_code

# renovate: datasource=github-releases depName=pingdotgg/t3code
t3_code_version = "0.0.33"
t3_code_checksum = "415c8648f43c3d22d572f27f2c50fdc8c310ea7fcde9537b903e1e2f1c8775a1"

if t3_code["enabled"]:
    version = t3_code_version
    checksum = t3_code_checksum

    local_bin_dir = f"/home/{user}/.local/bin"
    share_dir = f"/home/{user}/.local/share/t3-code"
    icon_base = f"/home/{user}/.local/share/icons/hicolor"
    pixmaps_dir = f"/home/{user}/.local/share/pixmaps"
    applications_dir = f"/home/{user}/.local/share/applications"

    app_image = f"{local_bin_dir}/T3-Code.AppImage"
    runner = f"{local_bin_dir}/t3-code"
    desktop_file = f"{applications_dir}/t3-code.desktop"
    icon_256 = f"{icon_base}/256x256/apps/t3-code.png"
    icon_512 = f"{icon_base}/512x512/apps/t3-code.png"
    pixmap_icon = f"{pixmaps_dir}/t3-code.png"

    for path in (
        local_bin_dir,
        share_dir,
        applications_dir,
        f"{icon_base}/256x256/apps",
        f"{icon_base}/512x512/apps",
        pixmaps_dir,
    ):
        files.directory(
            name="Ensure directory " + path,
            path=path,
            user=user,
            group=user,
            mode="755",
        )

    app_image_changed = files.download(
        name="Download T3 Code AppImage from pingdotgg/t3code",
        src=f"https://github.com/pingdotgg/t3code/releases/download/v{version}/T3-Code-{version}-x86_64.AppImage",
        dest=app_image,
        user=user,
        group=user,
        mode="755",
        sha256sum=checksum,
    )

    files.put(
        name="Install 256px icon",
        src=f"{dirname_of(__file__)}/files/icons/t3-code-256.png",
        dest=icon_256,
        user=user,
        group=user,
        mode="644",
    )

    files.put(
        name="Install 512px icon",
        src=f"{dirname_of(__file__)}/files/icons/t3-code-512.png",
        dest=icon_512,
        user=user,
        group=user,
        mode="644",
    )

    files.put(
        name="Install pixmaps icon",
        src=f"{dirname_of(__file__)}/files/icons/t3-code-256.png",
        dest=pixmap_icon,
        user=user,
        group=user,
        mode="644",
    )

    runner_script = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'APPIMAGE="{app_image}"\n'
        'if [[ ! -x "$APPIMAGE" ]]; then\n'
        "    printf 'T3 Code is not installed at %s\\n' \"$APPIMAGE\" >&2\n"
        "    exit 1\n"
        "fi\n"
        "# The bundled chrome-sandbox needs to be SUID root (mode 4755), which the\n"
        "# FUSE-mounted AppImage cannot provide, so disable Chromium sandboxing.\n"
        'ARGS=(--no-sandbox "$@")\n'
        "if command -v ldconfig >/dev/null 2>&1 && ldconfig -p 2>/dev/null | grep -q 'libfuse\\.so\\.2'; then\n"
        '    exec "$APPIMAGE" "${ARGS[@]}"\n'
        "fi\n"
        "for c in /lib/libfuse.so.2 /usr/lib/libfuse.so.2 /lib64/libfuse.so.2 /usr/lib64/libfuse.so.2; do\n"
        '    [[ -e "$c" ]] && exec "$APPIMAGE" "${ARGS[@]}"\n'
        "done\n"
        'exec "$APPIMAGE" --appimage-extract-and-run "${ARGS[@]}"\n'
    )
    files.put(
        name="Install FUSE-aware runner",
        src=io.StringIO(runner_script),
        dest=runner,
        user=user,
        group=user,
        mode="755",
    )

    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=T3 Code
Comment=AI coding assistant desktop app
Exec={runner}
TryExec={runner}
Icon=t3-code
Terminal=false
Categories=Development;IDE;
StartupNotify=true
StartupWMClass=T3 Code (Alpha)
"""
    files.put(
        name="Install .desktop launcher",
        src=io.StringIO(desktop_content),
        dest=desktop_file,
        user=user,
        group=user,
        mode="644",
    )

    server.shell(
        name="Refresh desktop and icon caches",
        commands=[
            f"update-desktop-database {applications_dir} 2>/dev/null || true",
            f"gtk-update-icon-cache -f -t {icon_base} >/dev/null 2>&1 || true",
        ],
        _if=lambda: app_image_changed.changed,
    )
