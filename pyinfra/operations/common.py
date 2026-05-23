from pyinfra import host
from pyinfra.operations import apt, files, server
from pyinfra.facts.files import File


def apt_install(packages: list, update: bool = True) -> None:
    if not packages:
        return
        
    apt.packages(
        name=f"Install packages: {', '.join(packages)}",
        packages=packages,
        update=update,
        present=True,
    )


def file_append(path: str, content: str) -> None:
    files.line(
        name=f"Append to {path}",
        path=path,
        line=content,
    )


def file_block(path: str, start_marker: str, end_marker: str, content: str) -> None:
    files.block(
        name=f"Manage block in {path}",
        path=path,
        block=content,
        marker_start=start_marker,
        marker_end=end_marker,
    )


def file_exists(path: str) -> bool:
    return host.get_fact(File, path=path) is not None


def command_execute(commands: str | list, description: str = None) -> None:
    server.shell(
        name=description or f"Execute: {commands}",
        commands=commands,
    )


def directory_create(path: str, user: str = None, group: str = None, mode: str = "755") -> None:
    files.directory(
        name=f"Create directory {path}",
        path=path,
        present=True,
        user=user,
        group=group,
        mode=mode,
    )