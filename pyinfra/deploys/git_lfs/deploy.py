from pyinfra import host
from pyinfra.operations import server

if host.data.get("git_lfs", {}).get("enabled", False):
    # Set defaults for git_lfs role
    git_lfs_defaults = {
        "git_lfs_version": "3.7.1",
        "git_lfs_checksum": "1c0b6ee5200ca708c5cebebb18fdeb0e1c98f1af5c1a9cba205a4c0ab5a5ec08",
    }
    
    # Combine defaults with host data
    git_lfs = git_lfs_defaults.copy()
    if host.data.get("git_lfs"):
        git_lfs.update(host.data.get("git_lfs", {}))

    # Install git-lfs using github_release_binary role
    # Note: This would be implemented as a separate operation or include
    # Since we're porting individual roles, we'll simulate the include
    url = f"https://github.com/git-lfs/git-lfs/releases/download/v{git_lfs['git_lfs_version']}/git-lfs-linux-amd64-v{git_lfs['git_lfs_version']}.tar.gz"
    binary_name = "git-lfs"
    binary_checksum = git_lfs["git_lfs_checksum"]
    tar_strip_components = 1
    
    # In a real implementation, this would use the github_release_binary operation
    # For now, we'll just log that it would be installed
    server.shell(
        name="Install git-lfs",
        commands=[f"echo 'Would install git-lfs from {url}'"],
    )