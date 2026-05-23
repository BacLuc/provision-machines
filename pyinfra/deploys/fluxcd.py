from pyinfra import host
from pyinfra.operations import files

user = host.data.get("user", "ubuntu")

if host.data.get("enable_fluxcd", False):
    
    files.block(
        name="Setup flux cli alias",
        path=f"/home/{user}/.bash_aliases",
        marker="# PYINFRA MANAGED BLOCK: flux cli alias",
        block="""alias flux='docker run --rm -it \\
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
    )
    
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Setup flux cli alias for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# PYINFRA MANAGED BLOCK: flux cli alias",
            block="""alias flux='docker run --rm -it \\
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
        )