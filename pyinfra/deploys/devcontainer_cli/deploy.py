from pyinfra import host
from pyinfra.operations import npm

if host.data.devcontainer_cli["enabled"]:
    npm.packages(
        name="Install devcontainer-cli",
        packages=["@devcontainers/cli"],
        _sudo=True,
    )
