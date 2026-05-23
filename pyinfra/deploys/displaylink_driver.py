from pyinfra import host
from pyinfra.operations import apt, files, server

if host.data.get("enable_displaylink_driver", False):
    
    server.shell(
        name="Check if DisplayLink driver is installed",
        commands=["dpkg -l | grep displaylink-driver && echo 'true' || echo 'false'"],
        ignore_errors=True,
        register="displaylink_driver_check",
    )
    
    # Install driver if not installed (simplified logic)
    files.download(
        name="Download Synaptics repository keyring",
        src="https://www.synaptics.com/sites/default/files/Ubuntu/pool/stable/main/all/synaptics-repository-keyring.deb",
        dest="/tmp/synaptics-repository-keyring.deb",
        mode="644",
    )
    
    apt.packages(
        name="Install Synaptics repository keyring",
        packages=["/tmp/synaptics-repository-keyring.deb"],
        _sudo=True,
    )
    
    apt.update(
        name="Update APT cache",
        _sudo=True,
    )
    
    apt.packages(
        name="Install DisplayLink driver",
        packages=["displaylink-driver"],
        _sudo=True,
    )