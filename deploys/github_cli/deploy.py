from pyinfra import host

from operations.github_release_binary import github_release_binary

github_cli = host.data.github_cli

if github_cli["enabled"]:
    # renovate: datasource=github-releases depName=cli/cli
    gh_version = "2.105.0"
    gh_checksum = "fa7cff06d4db9eee98e00b10ac93beebfe1822109ac04a6cbbf9d806c21d0073"

    github_release_binary(
        url=f"https://github.com/cli/cli/releases/download/v{gh_version}/gh_{gh_version}_linux_amd64.tar.gz",
        binary_name="gh",
        checksum=gh_checksum,
        strip_components=2,
    )
