import io

from pyinfra import host
from pyinfra.facts.files import File, Sha256File
from pyinfra.operations import files, server, snap

from operations.github_release_binary import github_release_binary
from operations.homebrew import HOMEBREW_BIN, user_brew_bin
from operations.user import get_user_name

user = get_user_name()
kubectl = host.data.kubectl

if kubectl["enabled"]:
    snap.package(
        name="Install kubectl",
        packages=["kubectl"],
        classic=True,
        _sudo=True,
    )

    snap.package(
        name="Install helm",
        packages=["helm"],
        classic=True,
        _sudo=True,
    )

    snap.package(
        name="Install yq",
        packages=["yq"],
        _sudo=True,
    )

    files.directory(
        name="Create kubeconfig directories",
        path=f"/home/{user}/.kube/config.d",
        user=user,
        group=user,
        mode="755",
    )

    context_management = """function ktx() {
  if [ $# -eq 0 ]; then
     kubectl config get-contexts
     return
  fi
  cat ${shell_tmp_dir}/.kube/config | yq '.current-context="'$1'"' | cat > ${shell_tmp_dir}/.kube/config
}

KUBECONFIG="$HOME/.kube/config.d/empty"
for file in $(find $HOME/.kube/config.d -type f); do
  KUBECONFIG="$KUBECONFIG:$file"
done

shell_tmp_dir=$(mktemp -d)
mkdir ${shell_tmp_dir}/.kube
yq eval -n ' .apiVersion="v1" | .current-context="" | .contexts=[] | .users=[] | .clusters=[] ' | cat  > ${shell_tmp_dir}/.kube/config
export KUBECONFIG="$KUBECONFIG:${shell_tmp_dir}/.kube/config"
export KUBECONFIG="${shell_tmp_dir}/.kube/config:$KUBECONFIG"
"""

    files.put(
        name="Add kubectl context management for bash",
        src=io.StringIO(context_management),
        dest=f"/home/{user}/.bashrc.d/kubectl-context.sh",
        user=user,
        group=user,
        mode="644",
    )

    files.put(
        name="Add kubectl completion for bash",
        src=io.StringIO("""\
source <(kubectl completion bash)
complete -F __start_kubectl k
"""),
        dest=f"/home/{user}/.bashrc.d/kubectl-completion.sh",
        user=user,
        group=user,
        mode="644",
    )

    if host.data.zsh["enabled"]:
        files.put(
            name="Add kubectl context management for zsh",
            src=io.StringIO(context_management),
            dest=f"/home/{user}/.zshrc.d/kubectl-context.zsh",
            user=user,
            group=user,
            mode="644",
        )

        files.put(
            name="Add kubectl completion for zsh",
            src=io.StringIO("""\
source <(kubectl completion zsh)
complete -F __start_kubectl k
[[ $commands[kubectl] ]] && source <(kubectl completion zsh)
"""),
            dest=f"/home/{user}/.zshrc.d/kubectl-completion.zsh",
            user=user,
            group=user,
            mode="644",
        )

    kubectl_aliases = [
        {"line": "alias k=kubectl", "regexp": "^alias k="},
        {"line": "alias ka='kubectl --as \"system:admin\"'", "regexp": "^alias ka="},
        {
            "line": 'alias kn=\'f() { [ "$1" ] && kubectl config set-context --current --namespace $1 || kubectl config view --minify | grep namespace | cut -d" " -f6 ; } ; f\'',
            "regexp": "^alias kn=",
        },
        {"line": "alias helma='helm --kube-as-user \"system:admin\"'", "regexp": "^alias helma="},
        {
            "line": "alias kgworld='kubectl get $(kubectl api-resources --verbs=list --namespaced -o name | paste -sd \",\")'",
            "regexp": "^alias kgworld=",
        },
        {
            "line": 'alias kagworld=\'kubectl --as "system:admin" get $(kubectl api-resources --verbs=list --namespaced -o name | paste -sd ",")\'',
            "regexp": "^alias kagworld=",
        },
        {"line": "alias k9sa='k9s --as \"system:admin\"'", "regexp": "^alias k9sa="},
    ]

    for alias in kubectl_aliases:
        files.line(
            name=f"Add kubectl alias: {alias['line']}",
            path=f"/home/{user}/.bash_aliases",
            line=alias["regexp"],
            replace=alias["line"],
            present=True,
        )

    brew_tools = ["k9s", "kubeconform", "kustomize", "kubeseal", "helmfile"]
    for tool in brew_tools:
        if host.get_fact(File, f"{HOMEBREW_BIN}/{tool}") is None:
            server.shell(
                name=f"Install {tool} via brew",
                commands=[user_brew_bin(user) + f" install {tool}"],
            )

    if kubectl["enable_oidc_plugin"] and host.get_fact(File, f"{HOMEBREW_BIN}/kubectl-oidc_login") is None:
        server.shell(
            name="Install kubelogin via brew",
            commands=[user_brew_bin(user) + " install kubelogin"],
        )

    # renovate: datasource=github-releases depName=jlandowner/helm-chartsnap
    helm_chartsnap_version = "0.6.0"
    helm_chartsnap_path = f"/home/{user}/.local/share/helm/plugins/helm-chartsnap/bin/chartsnap"
    helm_chartsnap_checksum = "3891bacb914c3f17f39c405682358f6c609720bd00387723723929c1053e8952"

    if host.get_fact(Sha256File, helm_chartsnap_path) != helm_chartsnap_checksum:
        server.shell(
            name="Install helm-chartsnap",
            commands=[
                "helm plugin uninstall chartsnap || true",
                f"helm plugin install --version {helm_chartsnap_version} https://github.com/jlandowner/helm-chartsnap --verify=false",
            ],
        )

    # renovate: datasource=github-releases depName=databus23/helm-diff
    helm_diff_version = "3.15.10"
    helm_diff_path = f"/home/{user}/.local/share/helm/plugins/helm-diff/bin/diff"
    helm_diff_checksum = "e3800f74f6271ded023fdf4cee56f8b314bbef3c20d360625610031349f4b63c"

    if host.get_fact(Sha256File, helm_diff_path) != helm_diff_checksum:
        server.shell(
            name="Install helm-diff",
            commands=[
                "helm plugin uninstall diff || true",
                f"helm plugin install --version {helm_diff_version} https://github.com/databus23/helm-diff --verify=false",
            ],
        )

    github_release_binary(
        url=f"https://github.com/itaysk/kubectl-neat/releases/download/v{kubectl['kubectl_neat_version']}/kubectl-neat_linux_amd64.tar.gz",
        binary_name="kubectl-neat",
        checksum="8dc3086fa8e7f5390f35a0b257566af478575ae3cc0d5b4614fbebbee5f35352",
    )

    github_release_binary(
        url=f"https://github.com/robscott/kube-capacity/releases/download/v{kubectl['kubectl_capacity_version']}/kube-capacity_v{kubectl['kubectl_capacity_version']}_linux_x86_64.tar.gz",
        binary_name="kube-capacity",
        checksum="c4e49762110584b2efbf5d4b0c69f549ef86275ac2ee5343a99e7522d3b38ae8",
    )

    github_release_binary(
        url=f"https://github.com/rajatjindal/kubectl-modify-secret/releases/download/v{kubectl['kubectl_modify_secret_version']}/kubectl-modify-secret_v{kubectl['kubectl_modify_secret_version']}_linux_amd64.tar.gz",
        binary_name="kubectl-modify_secret",
        checksum="be5a7fd276a35da9dfb1fd558a44245c111a787dd05d42d80ca9d6ece02107e5",
    )
