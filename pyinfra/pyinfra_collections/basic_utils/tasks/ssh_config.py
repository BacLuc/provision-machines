"""SSH config setup."""

from io import StringIO

from pyinfra.operations import files


def setup(user, home, paths_to_include):
    """Setup SSH config directory and main config file."""
    # Create config.d directory
    files.directory(
        name="Create SSH config.d directory",
        path=f"{home}/.ssh/config.d",
        mode="700",
    )

    # Create main SSH config file with includes
    include_content = ""
    for path in paths_to_include:
        include_content += f"Include {path}\n"

    files.put(
        name="Create SSH config file with includes",
        src=StringIO(include_content),
        dest=f"{home}/.ssh/config",
        mode="600",
    )
