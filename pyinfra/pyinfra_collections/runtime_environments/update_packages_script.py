"""Update packages scripts installation."""

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


@deploy("Update Packages Script")
def configure_update_packages_script(user=None, home=None, _sudo=None):
    """Install update packages scripts."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_update_packages_script", False)):
        return

    # Get configuration
    update_script_dir = host.data.get("update_packages_script_dir", "/usr/local/bin")

    # Create update scripts folder
    files.directory(
        name="Create update scripts folder",
        path=update_script_dir,
        present=True,
        mode="755",
    )

    # Create update-script.sh
    update_script_content = """#!/bin/bash
set -euo pipefail

echo "==> Updating package lists..."
sudo apt-get update

echo "==> Upgrading packages..."
sudo apt-get upgrade -y

echo "==> Distribution upgrade..."
sudo apt-get dist-upgrade -y

echo "==> Removing unnecessary packages..."
sudo apt-get autoremove -y

echo "==> Cleaning up..."
sudo apt-get autoclean

echo "==> Done!"
"""

    files.put(
        name="Create update script",
        src=StringIO(update_script_content),
        dest=f"{update_script_dir}/update-script",
        mode="755",
    )

    # Create apt-upgrade.sh
    apt_upgrade_content = """#!/bin/bash
set -euo pipefail

echo "==> Running apt upgrade..."
sudo apt-get upgrade -y
"""

    files.put(
        name="Create apt upgrade script",
        src=StringIO(apt_upgrade_content),
        dest=f"{update_script_dir}/apt-upgrade",
        mode="755",
    )
