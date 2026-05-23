from pyinfra import host
from pyinfra.operations import apt
from .github_release_binary import github_release_binary

lazygit_defaults = {
    # renovate: datasource=github-releases depName=jesseduffield/lazygit
    "lazygit_version": "0.61.1",
    "lazygit_checksum": "5c7c81884167cf38561c82704ec8783bcd199f484e6c63c781783f4f5a662a2a",
}

lazygit = lazygit_defaults.copy()
if host.data.get("lazygit"):
    lazygit.update(host.data.get("lazygit", {}))

if host.data.get("enable_lazygit", False):
    
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