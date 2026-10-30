from pyinfra import host

from operations.github_release_binary import github_release_binary

# renovate: datasource=github-releases depName=anchore/syft
syft_version = "1.55.0"
syft_checksum = "64c9631c3560336c55c549df0de08cd577d02399c9de807ac390960a4ed5c351"

syft = host.data.syft

if syft["enabled"]:
    github_release_binary(
        url=f"https://github.com/anchore/syft/releases/download/v{syft_version}/syft_{syft_version}_linux_amd64.tar.gz",
        binary_name="syft",
        checksum=syft_checksum,
    )
