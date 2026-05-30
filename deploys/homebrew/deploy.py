import io

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

from operations.homebrew import HOMEBREW_BIN, HOMEBREW_BREW_BIN, HOMEBREW_HOME, HOMEBREW_LINUXBREW, user_brew_bin
from operations.user import get_user_name

user = get_user_name()

if host.data.homebrew["enabled"]:
    homebrew_path = f"{HOMEBREW_LINUXBREW}/Homebrew/bin"
    user_id = host.get_fact(Command, "id -u")

    # renovate: datasource=docker depName=homebrew/brew
    homebrew_version = "4.6.14"

    files.directory(
        name="Create linuxbrew home dir",
        path=HOMEBREW_HOME,
        _sudo=True,
        mode="755",
    )

    files.directory(
        name="Create .linuxbrew dir",
        path=HOMEBREW_LINUXBREW,
        user=user,
        _sudo=True,
        mode="755",
    )

    files.directory(
        name="Create .cache dir",
        path=f"{HOMEBREW_HOME}/.cache",
        user=user,
        _sudo=True,
        mode="755",
    )

    files.directory(
        name="Setup user bin dir",
        path=f"/home/{user}/bin",
        user=user,
        group=user,
        mode="755",
    )

    install_brew = server.shell(
        name="Copy homebrew installation from container to host",
        commands=[
            f"""container_id=$(docker create homebrew/brew:{homebrew_version})
set +e
docker cp $container_id:{HOMEBREW_LINUXBREW} {HOMEBREW_HOME}/
exit_code=$?
docker rm $container_id
exit $exit_code"""
        ],
        _sudo=True,
        _if=lambda: host.get_fact(File, HOMEBREW_BREW_BIN) is None,
    )

    files.directory(
        name="Fix ownership of homebrew installation",
        path=HOMEBREW_LINUXBREW,
        user=user,
        group=user,
        recursive=True,
        _sudo=True,
        _if=lambda: install_brew.changed,
    )

    files.put(
        name="Create brew script",
        src=io.StringIO(
            f"""#!/bin/sh
HOMEBREW_VERSION={homebrew_version}
docker run --rm -v {HOMEBREW_HOME}:{HOMEBREW_HOME} --user {user_id} homebrew/brew:$HOMEBREW_VERSION brew "$@"
"""
        ),
        dest=user_brew_bin(user),
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Add homebrew to path in bash",
        src=io.StringIO(f'PATH="$PATH:{homebrew_path}:{HOMEBREW_BIN}"\n'),
        dest=f"/home/{user}/.bashrc.d/homebrew-path.sh",
        user=user,
        group=user,
        mode="644",
    )
