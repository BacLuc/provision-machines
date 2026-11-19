from pyinfra import host

from operations.github_release_binary import github_release_binary

# renovate: datasource=github-releases depName=anchore/syft
syft_version = "1.57.2"
syft_checksum = "17cc40c1e40bfdeb8c84b6d9928909bceb793f22e8a8023ef408625f1d96ec5"

syft = host.data.syft

if syft["enabled"]:
    github_release_binary(
        url=f"https://github.com/anchore/syft/releases/download/v{syft_version}/syft_{syft_version}_linux_amd64.tar.gz",
        binary_name="syft",
        checksum=syft_checksum,
    )
