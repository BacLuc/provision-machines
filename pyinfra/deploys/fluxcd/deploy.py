from pyinfra import host
from pyinfra.operations import files

# Get user from host data
user = host.data.get("user", "ubuntu")

if host.data.get("fluxcd", {}).get("enabled", False):
    # Setup flux cli alias
    files.block(
        name="Setup flux cli alias",
        path=f"/home/{user}/.bash_aliases",
        marker="# ANSIBLE MANAGED BLOCK: flux cli alias",
        content="""alias flux='docker run --rm -it \\
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
  ghcr.io/fluxcd/flux-cli:${FLUX_CLI_VERSION:-v2.2.3} --kubeconfig=/kubeconfig --as "system:admin"'""",
        user=user,
        group=user,
    )