from pyinfra import host
from pyinfra.operations import files, server

user = host.data.get("user", "ubuntu")
user_id = host.data.get("user_id", "1000")

homebrew_home = "/home/linuxbrew"
homebrew_binaries_path = "/home/linuxbrew/.linuxbrew/bin"
homebrew_path = "/home/linuxbrew/.linuxbrew/Homebrew/bin"

if host.data.get("homebrew", {}).get("enabled", False):
    
    files.directory(
        name="Create linuxbrew home dir",
        path=homebrew_home,
        _sudo=True,
        mode="755",
    )
    
    files.directory(
        name="Create .linuxbrew dir",
        path=f"{homebrew_home}/.linuxbrew",
        _sudo=True,
        user=user,
        mode="755",
    )
    
    files.directory(
        name="Create .cache dir",
        path=f"{homebrew_home}/.cache",
        _sudo=True,
        user=user,
        mode="755",
    )
    
    files.directory(
        name="Setup user bin dir",
        path=f"/home/{user}/bin",
        mode="755",
    )
    
    files.file(
        name="Check if homebrew is already installed",
        path=f"{homebrew_binaries_path}/brew",
    )
    
    server.shell(
        name="Copy homebrew installation using docker cp and tar",
        commands=[
            "HOMEBREW_VERSION=4.6.14",
            "container_id=$(docker create homebrew/brew:$HOMEBREW_VERSION)",
            "set +e",
            f"docker cp $container_id:/home/linuxbrew/.linuxbrew {homebrew_home}/",
            "exit_code=$?",
            "docker rm $container_id",
            "exit $exit_code",
        ],
        _sudo=True,
    )
    
    files.directory(
        name="Fix ownership of homebrew installation",
        path=f"{homebrew_home}/.linuxbrew",
        _sudo=True,
        user=user,
        group=user,
        recursive=True,
    )
    
    files.put(
        name="Create brew script",
        dest=f"/home/{user}/bin/brew",
        content=f"""#!/bin/sh
HOMEBREW_VERSION=4.6.14
docker run --rm -v {homebrew_home}:{homebrew_home} --user {user_id} homebrew/brew:$HOMEBREW_VERSION brew "$@"
""",
        mode="755",
    )
    
    files.block(
        name="Add homebrew to path",
        path=f"/home/{user}/.bashrc",
        marker="# PYINFRA MANAGED BLOCK: homebrew",
        block=f"""PATH="$PATH:{homebrew_path}:{homebrew_binaries_path}\"""",
    )
    
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Add homebrew to path for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# PYINFRA MANAGED BLOCK: homebrew",
            block=f"""PATH="$PATH:{homebrew_path}:{homebrew_binaries_path}\"""",
        )