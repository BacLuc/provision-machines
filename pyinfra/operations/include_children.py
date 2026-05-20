import os

from pyinfra import local, logger


def include_children(directory: str) -> None:
    if not os.path.isdir(directory):
        logger.info(f"Directory {directory} does not exist or is not a directory")
        return

    for child_dir in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, child_dir)) and os.path.exists(
            os.path.join(directory, child_dir, "deploy.py")
        ):
            print(f"including {child_dir}")
            local.include(filename=os.path.join(directory, child_dir, "deploy.py"))
