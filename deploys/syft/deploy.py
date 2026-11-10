from pyinfra import host

from operations.github_release_binary import github_release_binary

# renovate: datasource=github-releases depName=anchore/syft
syft_version = "1.57.1"
syft_checksum = "de3982edbbc250c4a40764c7b1f30bbf54b681f9b99391ee6b85bfdfa5d4dffe"

syft = host.data.syft

if syft["enabled"]:
    github_release_binary(
        url=f"https://github.com/anchore/syft/releases/download/v{syft_version}/syft_{syft_version}_linux_amd64.tar.gz",
        binary_name="syft",
        checksum=syft_checksum,
    )
