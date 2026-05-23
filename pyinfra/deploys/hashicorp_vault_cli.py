from pyinfra import host
from pyinfra.operations import apt
from .hashicorp_apt_repo import hashicorp_apt_repo

if host.data.get("enable_hashicorp_vault_cli", False):
    
    hashicorp_apt_repo()
    
    apt.packages(
        name="Install vault",
        packages=["vault"],
        _sudo=True,
    )