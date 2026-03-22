"""Setup bat command symlink."""

from pyinfra.operations import files


def setup(user, home):
    """Setup bat command by creating symlink from batcat to bat."""
    files.link(
        name="Create symbolic link for batcat to bat",
        target=f"{home}/bin/bat",
        source="/usr/bin/batcat",
        present=True,
    )
