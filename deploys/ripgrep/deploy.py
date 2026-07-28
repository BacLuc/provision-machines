from pyinfra import host

from operations.github_release_binary import github_release_binary

ripgrep = host.data.ripgrep

if ripgrep["enabled"]:
    github_release_binary(
        url=f"https://github.com/BurntSushi/ripgrep/releases/download/{ripgrep['ripgrep_version']}/ripgrep-{ripgrep['ripgrep_version']}-x86_64-unknown-linux-musl.tar.gz",
        binary_name="rg",
        checksum=ripgrep["ripgrep_checksum"],
        strip_components=1,
    )
