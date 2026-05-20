import os
import sys

from pyinfra import host
from pyinfra.operations import apt, files, server

# Add the current directory to sys.path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    additional_tools,
    basic_tools,
    locale,
    timezone,
)

# Check if basicsetup is enabled
if host.data.get("basicsetup", {}).get("enabled", True):
    # Get configuration from host data with defaults
    basic_tools = host.data.get("basicsetup", {}).get("basic_tools", basic_tools)
    additional_tools = host.data.get("basicsetup", {}).get("additional_tools", additional_tools)
    timezone = host.data.get("basicsetup", {}).get("timezone", timezone)
    locale = host.data.get("basicsetup", {}).get("locale", locale)

    # Install basic tools
    apt.packages(
        name="Install basic tools",
        packages=basic_tools,
        update=True,
        _sudo=True,
    )

    # Install additional tools
    apt.packages(
        name="Install additional tools",
        packages=additional_tools,
        _sudo=True,
    )

    # Set timezone using shell commands (for container compatibility)
    server.shell(
        name=f"Set timezone to {timezone}",
        commands=[
            f"ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime",
            f"echo '{timezone}' > /etc/timezone",
        ],
        _sudo=True,
    )

    # Configure locale using shell commands
    server.shell(
        name=f"Set locale to {locale}",
        commands=[
            f"update-locale LANG={locale}",
            f"locale-gen {locale}",
        ],
        _sudo=True,
    )
