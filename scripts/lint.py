#!/usr/bin/env -S uv run --script
import subprocess
import sys
from multiprocessing import Process

from isort.main import main as isort_main
from mypy.main import main as mypy_main
from ruff import find_ruff_bin


def run_mypi() -> None:
    sys.argv = ["mypy", "."]
    mypy_main()


def main() -> None:
    ruff_bin = find_ruff_bin()
    subprocess.run([ruff_bin, "format"], check=True)

    p = Process(target=run_mypi)
    p.start()
    p.join()

    sys.argv = ["isort", "."]
    isort_main()


if __name__ == "__main__":
    main()
