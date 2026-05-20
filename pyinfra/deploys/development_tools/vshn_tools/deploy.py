import os

from operations.github_release_binary import github_release_binary
from pyinfra import host
from pyinfra.facts.server import User
from pyinfra.operations.files import download
from pyinfra.operations.server import shell

enabled = host.data.vshn_tools["enabled"]
user_name = host.get_fact(User)

# renovate: datasource=github-releases depName=vshn/appcat-cli
appcat_cli_version = "0.5.0"
appcat_cli_checksum = "2141bf312b56ff7baf7727a98bbe0488dab7769162fb88e63255209e3e8140f1"

github_release_binary(
    url=f"https://github.com/vshn/appcat-cli/releases/download/v{appcat_cli_version}/appcat-cli_{appcat_cli_version}_linux_amd64.tar.gz",
    binary_name="appcat-cli",
    checksum=appcat_cli_checksum,
    _if=enabled,
)

# renovate: datasource=github-releases depName=vshn/k8ify
k8ify_version = "2.5.0"
k8ify_checksum = "f3605d34439c0bef36930c71ad2b066acc0ba821e68c98e764fffc1a66dcc3b9"

github_release_binary(
    url=f"https://github.com/vshn/k8ify/releases/download/v{k8ify_version}/k8ify_{k8ify_version}_linux_amd64.tar.gz",
    binary_name="k8ify",
    checksum=k8ify_checksum,
    _if=enabled,
)

# renovate: datasource=github-releases depName=jsonnet-bundler/jsonnet-bundler
jsonnet_bundler_version = "0.6.3"
jsonnet_bundler_checksum = "424be2836ffee389d93a8cb873eb891a69fef4509026c7c1a825943292b8c841"

download(
    name="Download jsonnet-bundler",
    src=f"https://github.com/projectsyn/jsonnet-bundler/releases/download/v{jsonnet_bundler_version}/jb_linux_amd64",
    dest=f"/home/{user_name}/bin/jb",
    mode="755",
    sha256sum=jsonnet_bundler_checksum,
    _if=lambda: enabled,
)

# Commodore Python version compatibility
commodore_python_version = 3.12

# noinspection PyUnusedImports
import deploys.development_tools.python.uv

shell(
    name="Install commodore",
    commands=f"/home/{user_name}/bin/uv  tool install --python=python{commodore_python_version} --python-preference=system syn-commodore",
    _if=[lambda: enabled, lambda: not os.path.exists(f"/home/{user_name}/.local/bin/commodore")],
)
