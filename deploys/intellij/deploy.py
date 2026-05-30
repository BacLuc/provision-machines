from pyinfra import host
from pyinfra.operations import files, server, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

user = get_user_name()

if host.data.jetbrains["enabled"]:
    files.directory(
        name="Create local bin directory",
        path=f"/home/{user}/.local/bin",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Copy VM settings script",
        src=f"{dirname_of(__file__)}/files/apply-vm-settings.sh",
        dest=f"/home/{user}/.local/bin/apply-vm-settings.sh",
        user=user,
        group=user,
        mode="755",
    )

    files.directory(
        name="Create systemd user config directory",
        path=f"/home/{user}/.config/systemd/user",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Copy systemd service file",
        src=f"{dirname_of(__file__)}/files/intellij-vm-settings.service",
        dest=f"/home/{user}/.config/systemd/user/intellij-vm-settings.service",
        user=user,
        group=user,
        mode="644",
    )

    systemd.service(
        name="Enable intellij-vm-settings service",
        service="intellij-vm-settings",
        user_mode=True,
        daemon_reload=True,
        enabled=True,
        running=True,
    )

    server.shell(
        name="Run script once to apply settings immediately",
        commands=[f"/home/{user}/.local/bin/apply-vm-settings.sh || true"],
    )
