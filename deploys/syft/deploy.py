from pyinfra import host

from operations.github_release_binary import github_release_binary

syft = host.data.syft

if syft["enabled"]:
    github_release_binary(
        url=f"https://github.com/anchore/syft/releases/download/v{syft['syft_version']}/syft_{syft['syft_version']}_linux_amd64.tar.gz",
        binary_name="syft",
        checksum=syft["syft_checksum"],
    )
