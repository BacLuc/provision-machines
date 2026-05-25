import os
from pathlib import Path


def dirname_of(path: str) -> str:
    current_file_path = os.path.abspath(path)
    return os.path.dirname(current_file_path)
