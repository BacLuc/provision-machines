from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
    server,
)

if host.data.get("displaylink_driver", {}).get("enabled", False):
    # Check if DisplayLink driver is installed
    result = server.shell(
        name="Check if DisplayLink driver is installed",
        commands=["dpkg -l | grep displaylink-driver && echo 'true' || echo 'false'"],
    )
    
    # If DisplayLink driver is not installed
    if "false" in result.stdout:
        # Download Synaptics repository keyring
        files.download(
            name="Download Synaptics repository keyring",
            src="https://www.synaptics.com/sites/default/files/Ubuntu/pool/stable/main/all/synaptics-repository-keyring.deb",
            dest="/tmp/synaptics-repository-keyring.deb",
            mode="644",
        )

        # Install Synaptics repository keyring
        apt.deb(
            name="Install Synaptics repository keyring",
            src="/tmp/synaptics-repository-keyring.deb",
            _sudo=True,
        )

        # Update APT cache
        apt.update(
            name="Update APT cache",
            _sudo=True,
        )

        # Install DisplayLink driver
        apt.packages(
            name="Install DisplayLink driver",
            packages=["displaylink-driver"],
            _sudo=True,
        )