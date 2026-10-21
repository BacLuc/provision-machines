from pyinfra import host

from operations.github_release_binary import github_release_binary

github_cli = host.data.github_cli

if github_cli["enabled"]:
    # renovate: datasource=github-releases depName=cli/cli
    gh_version = "2.103.0"
    gh_checksum = "011adf6809c50c89a70f2e367f2658a2fd7c2fcf7dfc705bfe8049e6e4c731b2"

    github_release_binary(
        url=f"https://github.com/cli/cli/releases/download/v{gh_version}/gh_{gh_version}_linux_amd64.tar.gz",
        binary_name="gh",
        checksum=gh_checksum,
        strip_components=2,
    )
