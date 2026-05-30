from operations.filesystem import dirname_of
from pyinfra import host
from pyinfra.operations import files, systemd

user = host.data.get("user", "ubuntu")

if host.data.jetbrains["enabled"]:
    files.directory(
        name="Create local bin directory",
        path=f"/home/{user}/.local/bin",
        mode="755",
    )

    files.put(
        name="Copy VM settings script",
        src=f"{dirname_of(__file__)}/files/apply-vm-settings.sh",
        dest=f"/home/{user}/.local/bin/apply-vm-settings.sh",
        mode="755",
    )

    files.directory(
        name="Create systemd user config directory",
        path=f"/home/{user}/.config/systemd/user",
        mode="755",
    )

    files.put(
        name="Copy systemd service file",
        src=f"{dirname_of(__file__)}/files/intellij-vm-settings.service",
        dest=f"/home/{user}/.config/systemd/user/intellij-vm-settings.service",
        mode="644",
    )

    systemd.daemon_reload(
        name="Reload systemd user daemon",
        user_mode=True,
        _sudo=True,
        _sudo_user=user,
    )

    systemd.service(
        name="Enable intellij-vm-settings service",
        service="intellij-vm-settings",
        running=True,
        enabled=True,
        user_mode=True,
        _sudo=True,
        _sudo_user=user,
    )
