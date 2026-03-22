"""Python setup and configuration."""

import os

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, files, server


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Python")
def configure_python(user=None, home=None, venvs=None, pyenv_dir=None, _sudo=None, **kwargs):
    """Setup Python with virtual environments."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_python", False)):
        return

    # Get user/home from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    if home is None:
        home = f"/home/{user}"

    if venvs is None:
        venvs = host.data.get("python", {}).get("venvs", [])

    if pyenv_dir is None:
        pyenv_dir = f"{home}/pyenv"

    # Install Python packages
    apt.packages(
        name="Install Python packages",
        packages=["python3", "python3-pip", "python3-venv"],
        update=True,
    )

    # Setup python alternative to point to python3
    server.shell(
        name="Add python alternative for python3",
        commands=[
            "update-alternatives --install /usr/bin/python python /usr/bin/python3 1 || true"
        ],
    )

    server.shell(
        name="Set python3 as default python",
        commands=["update-alternatives --set python /usr/bin/python3 || true"],
    )

    # Create pyenv directory
    files.directory(
        name="Create pyenv directory",
        path=pyenv_dir,
        mode="755",
        user=user,
        group=user,
    )

    # Create virtual environments
    for venv_item in venvs:
        # Handle both string and dict formats
        if isinstance(venv_item, dict):
            venv_name = venv_item.get("name", "default")
        else:
            venv_name = venv_item

        venv_path = f"{pyenv_dir}/{venv_name}"
        activate_path = f"{venv_path}/bin/activate"

        # Create virtual environment (only if not already exists)
        server.shell(
            name=f"Create Python virtual environment: {venv_name}",
            commands=[f"test -f {activate_path} || python -m venv {venv_path}"],
        )

        # Make activate script executable
        files.file(
            name=f"Make activate script executable for {venv_name}",
            path=activate_path,
            mode="755",
            user=user,
            group=user,
        )
