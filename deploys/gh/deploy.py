from pyinfra import host

from operations.github_release_binary import github_release_binary

gh = host.data.gh

if gh["enabled"]:
    github_release_binary(
        url=f"https://github.com/cli/cli/releases/download/v{gh['gh_version']}/gh_{gh['gh_version']}_linux_amd64.tar.gz",
        binary_name="gh",
        checksum=gh["gh_checksum"],
        strip_components=2,
        tar_member=f"gh_{gh['gh_version']}_linux_amd64/bin/gh",
    )
