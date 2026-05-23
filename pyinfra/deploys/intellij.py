from pyinfra import host
from pyinfra.operations import files, server, systemd

user = host.data.get("user", "ubuntu")

if host.data.get("enable_jetbrains", False):
    
    files.directory(
        name="Create local bin directory",
        path=f"/home/{user}/.local/bin",
        mode="755",
    )
    
    files.put(
        name="Copy VM settings script",
        dest=f"/home/{user}/.local/bin/apply-vm-settings.sh",
        content="#!/bin/sh\n# VM settings script would go here",
        mode="755",
    )
    
    files.directory(
        name="Create systemd user config directory",
        path=f"/home/{user}/.config/systemd/user",
        mode="755",
    )
    
    files.put(
        name="Copy systemd service file",
        dest=f"/home/{user}/.config/systemd/user/intellij-vm-settings.service",
        content="""[Unit]
Description=Apply IntelliJ VM Settings

[Service]
Type=oneshot
ExecStart=%h/.local/bin/apply-vm-settings.sh
RemainAfterExit=yes

[Install]
WantedBy=default.target
""",
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
    
    server.shell(
        name="Run script once to apply settings immediately",
        commands=[f"{host.data.get('home', f'/home/{user}')}/.local/bin/apply-vm-settings.sh"],
    )