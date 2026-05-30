#!/usr/bin/env -S uv run --script

import sys

from pyinfra_cli.main import main as pyinfra_main


def main() -> None:
    sys.argv = ["pyinfra", "inventory.py", "run.py", "-y"]

    sys.exit(pyinfra_main())


if __name__ == "__main__":
    main()
