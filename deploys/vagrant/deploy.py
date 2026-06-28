from operations.filesystem import DEPLOYS_DIR
from pyinfra import host, local
from pyinfra.operations import apt

if host.data.vagrant["enabled"]:
    local.include(f"{DEPLOYS_DIR}/hashicorp_apt_repo/deploy.py")

    apt.packages(
        name="Install vagrant",
        packages=["vagrant"],
        _sudo=True,
    )
