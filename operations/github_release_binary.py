import tempfile
from typing import Callable, Union

from pyinfra import host, logger
from pyinfra.facts.files import Sha256File
from pyinfra.facts.server import User
from pyinfra.operations.files import directory, download
from pyinfra.operations.server import shell


def github_release_binary(
    url: str,
    binary_name: str,
    checksum: str,
    strip_components: int = 0,
    is_tar: bool = True,
    _if: Union[bool, Callable[[], bool]] = True,
) -> None:
    if not url:
        raise ValueError("URL cannot be empty")
    if not binary_name:
        raise ValueError("Binary name cannot be empty")
    if not checksum:
        raise ValueError("Checksum cannot be empty")
    if strip_components < 0:
        raise ValueError("Strip components cannot be negative")

    if isinstance(_if, bool) and not _if:
        return

    if callable(_if) and not _if():
        return

    user_name = host.get_fact(User)
    dest_file_path = f"/home/{user_name}/bin/{binary_name}"
    try:
        directory(
            name=f"Ensure /home/{user_name}/bin",
            path=f"/home/{user_name}/bin",
            present=True,
            user=user_name,
            group=user_name,
            mode="755",
        )

        file_checksum = host.get_fact(Sha256File, path=dest_file_path)
        if file_checksum == checksum:
            return

        # download file from url to temporary file
        with tempfile.NamedTemporaryFile() as temp_file:
            tmp_file_name = temp_file.name
            download(
                name=f"Create {tmp_file_name}",
                src=url,
                dest=tmp_file_name,
                mode="755",
                user=user_name,
                group=user_name,
            )

            if not is_tar:
                shell(
                    name=f"Install binary {binary_name}",
                    commands=[
                        f"cp {tmp_file_name} {dest_file_path}",
                        f"chmod u=rwx,go=rx {dest_file_path}",
                    ],
                )
                return

            strip_components_arg = f" --strip-components={strip_components}" if strip_components > 0 else ""
            shell(
                name=f"Extract binary file {binary_name} from tar {tmp_file_name}",
                commands=f"tar -xf {tmp_file_name} {strip_components_arg} -C /home/{user_name}/bin",
            )
    finally:
        file_checksum = host.get_fact(Sha256File, path=dest_file_path)
        if file_checksum != checksum:
            logger.warning(f"Checksum mismatch for {binary_name}, expected {checksum} but got {file_checksum}")
