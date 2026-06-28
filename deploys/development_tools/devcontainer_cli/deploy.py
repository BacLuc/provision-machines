from operations.filesystem import DEPLOYS_DIR
from pyinfra import host, local
from pyinfra.operations import npm

if host.data.devcontainer_cli["enabled"]:
    local.include(f"{DEPLOYS_DIR}/docker/deploy.py")
    local.include(f"{DEPLOYS_DIR}/development_tools/nvm/deploy.py")
    npm.packages(
        name="Install devcontainer-cli",
        packages=["@devcontainers/cli"],
        _sudo=host.data.nvm["_sudo_for_global_install"],
    )
