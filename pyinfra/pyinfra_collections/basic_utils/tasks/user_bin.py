"""User bin directory setup."""

from pyinfra.operations import files


def setup(user, home):
    """Setup user bin directory and PATH in shell configs."""
    # Create user bin directory
    files.directory(
        name="Create user bin directory",
        path=f"{home}/bin",
        mode="755",
        present=True,
    )

    # Add bin to PATH in bashrc
    files.block(
        name="Add bin to PATH in bashrc",
        path=f"{home}/.bashrc",
        content=f'export PATH="{home}/bin:$PATH"',
        marker="# {mark} ANSIBLE MANAGED BLOCK: bin of user",
    )
