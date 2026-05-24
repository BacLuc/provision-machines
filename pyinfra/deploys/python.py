from pyinfra import host
from pyinfra.operations import apt, files, server
from pyinfra.facts.server import User

from ..operations.github_release_binary import github_release_binary


def python():
    python_config = host.data.get("python", {})
    basic_utils_config = host.data.get("basic_utils", {})
    
    if not (python_config.get("enabled", False) or basic_utils_config.get("python", {}).get("enabled", False)):
        return

    python_defaults = {
        "venvs": [],
        "uv": {
            "version": "0.6.0",
            "checksum": "becf19e97d1fd659d2ad44c3e753ab5f3dd6551de64e39241170ae883ce570a2",
            "uvx_checksum": "80ad7e812aac189dedf7451e1680640a013adaebece2844489b8b5321ed3f27f",
        },
    }
    
    python_config = {**python_defaults, **python_config}

    apt.packages(
        name="Install python packages",
        packages=["python3", "python3-pip", "python3-venv"],
        _sudo=True,
    )

    server.shell(
        name="Add python3 to update-alternatives",
        commands=["update-alternatives --install /usr/bin/python python /usr/bin/python3 1"],
        _sudo=True,
    )

    current_python_link = host.get_fact(
        server.ShellCommand,
        command="update-alternatives --query python | grep 'current link' | awk '{print $NF}'",
        _sudo=True,
    )

    if current_python_link.strip() != "/usr/bin/python3":
        server.shell(
            name="Set python3 as default",
            commands=["update-alternatives --set python /usr/bin/python3"],
            _sudo=True,
        )

    if basic_utils_config.get("enable_ssh_config_dir", False):
        user_name = host.get_fact(User)
        files.directory(
            name="Create pyenv directory",
            path=f"/home/{user_name}/pyenv",
            mode="755",
        )

    venvs = python_config.get("venvs", [])
    for venv in venvs:
        user_name = host.get_fact(User)
        server.shell(
            name=f"Create Python virtual environment {venv}",
            commands=[
                f"python -m venv ~/pyenv/{venv}",
                f"chmod +x ~/pyenv/{venv}/bin/activate",
            ],
        )

    uv_config = python_config.get("uv", {})
    uv_version = uv_config.get("version")
    uv_checksum = uv_config.get("checksum")
    uvx_checksum = uv_config.get("uvx_checksum")

    github_release_binary(
        url=f"https://releases.astral.sh/github/uv/releases/download/{uv_version}/uv-x86_64-unknown-linux-gnu.tar.gz",
        binary_name="uv",
        checksum=uv_checksum,
        strip_components=1,
    )

    github_release_binary(
        url=f"https://releases.astral.sh/github/uv/releases/download/{uv_version}/uv-x86_64-unknown-linux-gnu.tar.gz",
        binary_name="uvx",
        checksum=uvx_checksum,
        strip_components=1,
    )