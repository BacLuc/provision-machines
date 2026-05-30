import os


def dirname_of(path: str) -> str:
    current_file_path = os.path.abspath(path)
    return os.path.dirname(current_file_path)


BASE_DIR = dirname_of(f"{__file__}/..")
DEPLOYS_DIR = f"{BASE_DIR}/deploys"
