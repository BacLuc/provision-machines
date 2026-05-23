from pyinfra import host
from pyinfra.operations import apt

if host.data.get("enable_ubuntu_cleanup", True):
    
    apt.packages(
        name="Remove no more referenced packages",
        autoremove=True,
        _sudo=True,
    )