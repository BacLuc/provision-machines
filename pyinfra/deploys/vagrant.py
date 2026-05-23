from pyinfra import host
from pyinfra.operations import apt
from .hashicorp_apt_repo import hashicorp_apt_repo

if host.data.get("enable_vagrant", False):
    
    hashicorp_apt_repo()
    
    apt.packages(
        name="Install vagrant",
        packages=["vagrant"],
        _sudo=True,
    )