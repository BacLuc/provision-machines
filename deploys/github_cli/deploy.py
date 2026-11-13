from pyinfra import host

from operations.github_release_binary import github_release_binary

github_cli = host.data.github_cli

if github_cli["enabled"]:
    # renovate: datasource=github-releases depName=cli/cli
    gh_version = "2.104.0"
    gh_checksum = "fca7ac8a8386e3ad65c9a96a96cbf272d1dcc4f76de174dae91d54e50729e240"

    github_release_binary(
        url=f"https://github.com/cli/cli/releases/download/v{gh_version}/gh_{gh_version}_linux_amd64.tar.gz",
        binary_name="gh",
        checksum=gh_checksum,
        strip_components=2,
    )
