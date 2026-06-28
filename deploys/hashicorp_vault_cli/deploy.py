from pyinfra import host, local
from pyinfra.operations import apt

from operations.filesystem import DEPLOYS_DIR

if host.data.hashicorp_vault_cli["enabled"]:
    local.include(f"{DEPLOYS_DIR}/hashicorp_apt_repo/deploy.py")

    apt.packages(
        name="Install vault",
        packages=["vault"],
        _sudo=True,
    )
