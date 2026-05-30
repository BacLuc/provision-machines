from pyinfra import host
from pyinfra.operations import files, server
from operations.github_release_binary import github_release_binary

user = host.data.get("user", "ubuntu")

kubectl_defaults = {
    # renovate: datasource=github-releases depName=itaysk/kubectl-neat
    "kubectl_neat_version": "2.0.4",
    # renovate: datasource=github-releases depName=robscott/kube-capacity
    "kubectl_capacity_version": "0.8.0",
    # renovate: datasource=github-releases depName=rajatjindal/kubectl-modify-secret
    "kubectl_modify_secret_version": "0.0.47",
    "contex_management_part": """
function ktx() {
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
""",
}

kubectl = {**kubectl_defaults, **host.data.kubectl}

if host.data.kubectl["enabled"]:
    server.shell(
        name="Install kubectl and helm",
        commands=["snap install kubectl --classic", "snap install helm --classic"],
        _sudo=True,
    )

    server.shell(
        name="Install yq",
        commands=["snap install yq"],
        _sudo=True,
    )

    files.directory(
        name="Create kubeconfig directories",
        path=f"/home/{user}/.kube/config.d",
        user=user,
        group=user,
        mode="755",
    )

    files.block(
        name="Source kubectl tools in bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: kubectl context",
        content=kubectl["contex_management_part"],
    )

    if host.data.zsh["enabled"]:
        files.block(
            name="Source kubectl tools in zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: kubectl context",
            content=kubectl["contex_management_part"],
        )

    files.block(
        name="Add kubectl completion for bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: kubectl completion",
        content="""source <(kubectl completion bash)
complete -F __start_kubectl k""",
    )

    if host.data.zsh["enabled"]:
        files.block(
            name="Add kubectl completion for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: kubectl completion",
            content="""source <(kubectl completion zsh)
complete -F __start_kubectl k
[[ $commands[kubectl] ]] && source <(kubectl completion zsh)""",
            try_prevent_shell_expansion=True,
        )

    bash_aliases = [
        {"regex": "^alias k=", "line": "alias k=kubectl"},
        {"regex": "^alias ka=", "line": 'alias ka=\'kubectl --as "system:admin"\''},
        {
            "regex": "^alias kn=",
            "line": 'alias kn=\'f() { [ "$1" ] && kubectl config set-context --current --namespace $1 || kubectl config view --minify | grep namespace | cut -d" " -f6 ; } ; f\'',
        },
        {
            "regex": "^alias helma=",
            "line": 'alias helma=\'helm --kube-as-user "system:admin"\'',
        },
        {
            "regex": "^alias kgworld=",
            "line": 'alias kgworld=\'kubectl get $(kubectl api-resources --verbs=list --namespaced -o name | paste -sd ",")\'',
        },
        {
            "regex": "^alias kagworld=",
            "line": 'alias kagworld=\'kubectl --as "system:admin" get $(kubectl api-resources --verbs=list --namespaced -o name | paste -sd ",")\'',
        },
    ]

    for alias in bash_aliases:
        files.line(
            name=f"Add alias: {alias['line']}",
            path=f"/home/{user}/.bash_aliases",
            line=alias["line"],
            replace=alias["regex"],
        )

    homebrew_binaries_path = host.data.homebrew.get("binaries_path", "/home/linuxbrew/.linuxbrew/bin")

    server.shell(
        name="Install k9s",
        commands=[f"{homebrew_binaries_path}/brew install k9s"],
    )

    files.line(
        name="Add k9s alias",
        path=f"/home/{user}/.bash_aliases",
        line='alias k9sa=\'k9s --as "system:admin"\'',
        replace="^alias k9sa=",
    )

    for tool, condition in [
        ("kubelogin", kubectl.get("enable_oidc_plugin", False)),
        ("kubeconform", True),
        ("kustomize", True),
        ("kubeseal", True),
        ("helmfile", True),
    ]:
        if condition:
            server.shell(
                name=f"Install {tool}",
                commands=[f"{homebrew_binaries_path}/brew install {tool}"],
            )

    helm_plugins = [
        {
            "name": "helm-chartsnap",
            "path": f"/home/{user}/.local/share/helm/plugins/helm-chartsnap/bin/chartsnap",
            "checksum": "3891bacb914c3f17f39c405682358f6c609720bd00387723723929c1053e8952",
            # renovate: datasource=github-releases depName=jlandowner/helm-chartsnap
            "version": "0.6.0",
            "url": "https://github.com/jlandowner/helm-chartsnap",
        },
        {
            "name": "helm-diff",
            "path": f"/home/{user}/.local/share/helm/plugins/helm-diff/bin/diff",
            "checksum": "e3800f74f6271ded023fdf4cee56f8b314bbef3c20d360625610031349f4b63c",
            # renovate: datasource=github-releases depName=databus23/helm-diff
            "version": "3.15.6",
            "url": "https://github.com/databus23/helm-diff",
        },
    ]

    for plugin in helm_plugins:
        server.shell(
            name=f"Install {plugin['name']}",
            commands=[
                f"helm plugin uninstall {plugin['name'].replace('helm-', '')} || true",
                f"helm plugin install --version {plugin['version']} {plugin['url']} --verify=false",
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
        binary_name="kubectl-modify-secret",
        checksum="be5a7fd276a35da9dfb1fd558a44245c111a787dd05d42d80ca9d6ece02107e5",
    )
