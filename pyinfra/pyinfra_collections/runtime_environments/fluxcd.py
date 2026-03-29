"""FluxCD installation and configuration."""

import os

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import files


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("FluxCD")
def configure_fluxcd(user=None, home=None, _sudo=None):
    """Configure FluxCD CLI aliases."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_fluxcd", False)):
        return

    home = home or os.path.expanduser("~")
    bash_aliases = os.path.join(home, ".bash_aliases")

    # Ensure .bash_aliases exists
    files.file(
        name="Ensure .bash_aliases exists",
        path=bash_aliases,
        present=True,
    )

    # Add flux CLI alias
    files.line(
        name="Add flux CLI alias",
        path=bash_aliases,
        line="alias flux='docker run --rm -it --user $UID --volume $KUBECONFIG:/kubeconfig --volume $PWD:/workspace --workdir $PWD:/workspace ghcr.io/fluxcd/flux-cli:${FLUX_CLI_VERSION:-v2.2.3} --kubeconfig=/kubeconfig'",
        ensure_newline=True,
    )

    # Add fluxa (flux as admin) alias
    files.line(
        name="Add fluxa CLI alias",
        path=bash_aliases,
        line="alias fluxa='docker run --rm -it --user $UID --volume $KUBECONFIG:/kubeconfig --volume $PWD:/workspace --workdir $PWD:/workspace ghcr.io/fluxcd/flux-cli:${FLUX_CLI_VERSION:-v2.2.3} --kubeconfig=/kubeconfig --as \"system:admin\"'",
        ensure_newline=True,
    )
