from pyinfra import host

from operations.github_release_binary import github_release_binary

git_lfs = host.data.git_lfs

if git_lfs["enabled"]:
    github_release_binary(
        url=f"https://github.com/git-lfs/git-lfs/releases/download/v{git_lfs['git_lfs_version']}/git-lfs-linux-amd64-v{git_lfs['git_lfs_version']}.tar.gz",
        binary_name="git-lfs",
        checksum=git_lfs["git_lfs_checksum"],
        strip_components=1,
    )
