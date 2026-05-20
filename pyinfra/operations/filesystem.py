import os

from path import Path


def dirname_of(path: str) -> str:
    current_file_path = os.path.abspath(path)
    return os.path.dirname(Path(current_file_path))
