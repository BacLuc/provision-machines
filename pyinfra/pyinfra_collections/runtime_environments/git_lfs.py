"""Git LFS installation and configuration."""

import os
from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server, files


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Git LFS")
def configure_git_lfs(user=None, home=None, _sudo=None):
    """Install and configure Git LFS."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_git_lfs", False)):
        return

    # Get configuration with defaults
    git_lfs_version = host.data.get("git_lfs_version", "3.7.1")
    git_lfs_checksum = host.data.get(
        "git_lfs_checksum",
        "1c0b6ee5200ca708c5cebebb18fdeb0e1c98f1af5c1a9cba205a4c0ab5a5ec08",
    )

    # Ensure ~/bin exists
    home = home or os.path.expanduser("~")
    bin_dir = os.path.join(home, "bin")

    files.directory(
        name="Create ~/bin directory",
        path=bin_dir,
        present=True,
        mode="755",
    )

    # Download and install git-lfs
    binary_path = os.path.join(bin_dir, "git-lfs")

    server.shell(
        name="Download and install git-lfs",
        commands=[
            f"curl -fsSL https://github.com/git-lfs/git-lfs/releases/download/v{git_lfs_version}/git-lfs-linux-amd64-v{git_lfs_version}.tar.gz -o /tmp/git-lfs.tar.gz",
            f"tar -xzf /tmp/git-lfs.tar.gz -C {bin_dir} --strip-components=1",
            f"rm /tmp/git-lfs.tar.gz",
        ],
        _ignore_errors=True,
    )

    # Make binary executable
    server.shell(
        name="Make git-lfs executable",
        commands=[f"chmod 755 {binary_path}"],
    )

    # Run git lfs install
    server.shell(
        name="Install git-lfs git configuration",
        commands=["git lfs install"],
        _ignore_errors=True,
    )
