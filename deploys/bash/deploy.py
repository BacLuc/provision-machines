from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
    server,
)

from operations.filesystem import BASE_DIR
from operations.user import get_user_name

user = get_user_name()

# renovate: datasource=docker depName=ghcr.io/bacluc/prettier-image/prettier-image
bash_prettier_image_version = "3.8.4"

if host.data.bash["enabled"]:
    apt.packages(
        name="Install autojump",
        packages=["autojump"],
        _sudo=True,
    )

    files.directory(
        name="Ensure dotfiles directory exists",
        path=f"/home/{user}/.dotfiles",
        user=user,
        group=user,
        mode="755",
    )

    files.sync(
        name="Sync dotfiles repository",
        src=f"{BASE_DIR}/dotfiles/",
        dest=f"/home/{user}/.dotfiles",
        user=user,
        group=user,
    )

    server.shell(
        name="Run dotfiles installer",
        commands=[f"bash /home/{user}/.dotfiles/install.sh"],
        user=user,
    )
