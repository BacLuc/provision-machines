"""IntelliJ IDEA / JetBrains setup."""

import os
from io import StringIO

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server, files


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("IntelliJ / JetBrains")
def configure_intellij(user=None, home=None, _sudo=None):
    """Configure JetBrains Toolbox and IntelliJ VM settings."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_jetbrains", False)):
        return

    home = home or os.path.expanduser("~")
    local_bin = os.path.join(home, ".local", "bin")

    # Create local bin directory
    files.directory(
        name="Create local bin directory",
        path=local_bin,
        present=True,
        mode="755",
    )

    # Create systemd user config directory
    files.directory(
        name="Create systemd user config directory",
        path=f"{home}/.config/systemd/user",
        present=True,
        mode="755",
    )

    # VM settings script content
    vm_settings_script = """#!/bin/bash
# Apply IntelliJ VM settings

IDEA_VM_OPTIONS="$HOME/.idea/java.vmoptions"

if [ -f "$IDEA_VM_OPTIONS" ]; then
    # Ensure settings directory exists
    mkdir -p "$HOME/.config/JetBrains/IntelliJIdea/"

    # Copy VM options to JetBrains config
    cp "$IDEA_VM_OPTIONS" "$HOME/.config/JetBrains/IntelliJIdea/idea.vmoptions"
fi
"""

    files.put(
        name="Create VM settings script",
        src=StringIO(vm_settings_script),
        dest=f"{local_bin}/apply-vm-settings.sh",
        mode="755",
    )

    # Create systemd service file
    service_content = """[Unit]
Description=IntelliJ IDEA VM Settings

[Service]
Type=oneshot
ExecStart=%h/.local/bin/apply-vm-settings.sh
RemainAfterExit=yes

[Install]
WantedBy=default.target
"""

    files.put(
        name="Create systemd service file",
        src=StringIO(service_content),
        dest=f"{home}/.config/systemd/user/intellij-vm-settings.service",
        mode="644",
    )

    # Run the script
    server.shell(
        name="Apply VM settings",
        commands=[f"{local_bin}/apply-vm-settings.sh"],
        _ignore_errors=True,
    )
