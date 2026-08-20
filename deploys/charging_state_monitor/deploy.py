from pyinfra import host
from pyinfra.operations import apt, files, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

user = get_user_name()

if host.data.charging_state_monitor["enabled"]:
    apt.packages(
        name="Install charging state monitor dependencies",
        packages=["acpi", "libnotify-bin"],
        update=True,
        _sudo=True,
    )

    files.directory(
        name="Create local bin directory",
        path=f"/home/{user}/.local/bin",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Copy charging state monitor script",
        src=f"{dirname_of(__file__)}/files/charging-state-monitor.sh",
        dest=f"/home/{user}/.local/bin/charging-state-monitor.sh",
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
        name="Copy charging state monitor service file",
        src=f"{dirname_of(__file__)}/files/charging-state-monitor.service",
        dest=f"/home/{user}/.config/systemd/user/charging-state-monitor.service",
        user=user,
        group=user,
        mode="644",
    )

    systemd.service(
        name="Enable charging state monitor service",
        service="charging-state-monitor",
        user_mode=True,
        daemon_reload=True,
        enabled=True,
        running=True,
    )
