from pyinfra import host

from operations.github_release_binary import github_release_binary

github_cli = host.data.github_cli

if github_cli["enabled"]:
    # renovate: datasource=github-releases depName=cli/cli
    gh_version = "2.106.0"
    gh_checksum = "8b9e0e460b7373a42296b83d2683b12af7f2c6e0c7007d01252fc066acbf83cb"

    github_release_binary(
        url=f"https://github.com/cli/cli/releases/download/v{gh_version}/gh_{gh_version}_linux_amd64.tar.gz",
        binary_name="gh",
        checksum=gh_checksum,
        strip_components=2,
    )
