import io

from operations.user import get_user_name
from pyinfra import host
from pyinfra.operations import files

user = get_user_name()

if host.data.fluxcd["enabled"]:
    flux_aliases = """alias flux='docker run --rm -it \\
  --user $UID \\
  --volume $KUBECONFIG:/kubeconfig \\
  --volume $PWD:/workspace \\
  --workdir $PWD:/workspace \\
  ghcr.io/fluxcd/flux-cli:${FLUX_CLI_VERSION:-v2.2.3} --kubeconfig=/kubeconfig'

alias fluxa='docker run --rm -it \\
  --user $UID \\
  --volume $KUBECONFIG:/kubeconfig \\
  --volume $PWD:/workspace \\
  --workdir $PWD:/workspace \\
  ghcr.io/fluxcd/flux-cli:${FLUX_CLI_VERSION:-v2.2.3} --kubeconfig=/kubeconfig --as "system:admin"'
"""

    files.put(
        name="Add flux cli aliases",
        src=io.StringIO(flux_aliases),
        dest=f"/home/{user}/.bash_aliases.d/flux-aliases.sh",
        user=user,
        group=user,
        mode="644",
    )
