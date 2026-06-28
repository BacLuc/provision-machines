from operations.github_release_binary import github_release_binary
from pyinfra import host
from pyinfra.operations import apt

lazygit = host.data.lazygit

if lazygit["enabled"]:
    github_release_binary(
        url=f"https://github.com/jesseduffield/lazygit/releases/download/v{lazygit['lazygit_version']}/lazygit_{lazygit['lazygit_version']}_Linux_x86_64.tar.gz",
        binary_name="lazygit",
        checksum=lazygit["lazygit_checksum"],
    )

    apt.packages(
        name="Install wl-clipboard",
        packages=["wl-clipboard"],
        _sudo=True,
    )
