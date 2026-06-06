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
    helm_diff_checksum = "4128d6059d4dbeed97a1a67b53a8c621d90a2854a4688fd1e7f98e54bcd57f85"

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
