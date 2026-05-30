import io

from pyinfra import host
from pyinfra.operations import files, server

user = host.data.get("user", "ubuntu")
user_id = host.data.get("user_id", "1000")

homebrew_home = "/home/linuxbrew"
homebrew_binaries_path = "/home/linuxbrew/.linuxbrew/bin"
homebrew_path = "/home/linuxbrew/.linuxbrew/Homebrew/bin"

if host.data.homebrew["enabled"]:
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

    brew_script = (
        "#!/bin/sh\n"
        "HOMEBREW_VERSION=4.6.14\n"
        f'docker run --rm -v {homebrew_home}:{homebrew_home} --user {user_id} homebrew/brew:$HOMEBREW_VERSION brew "$@"\n'
    )
    files.put(
        name="Create brew script",
        src=io.StringIO(brew_script),
        dest=f"/home/{user}/bin/brew",
        mode="755",
    )

    files.block(
        name="Add homebrew to path in bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: homebrew",
        content=f'PATH="$PATH:{homebrew_path}:{homebrew_binaries_path}"',
        try_prevent_shell_expansion=True,
    )

    if host.data.zsh["enabled"]:
        files.block(
            name="Add homebrew to path in zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: homebrew",
            content=f'PATH="$PATH:{homebrew_path}:{homebrew_binaries_path}"',
            try_prevent_shell_expansion=True,
        )
