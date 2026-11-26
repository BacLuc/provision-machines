#!/usr/bin/env -S uv run --script

import os
import sys

from pyinfra_cli.main import main as pyinfra_main


def main() -> None:
    os.environ["PYINFRA_LOCAL"] = "1"
    sys.argv = ["pyinfra", "inventory.py", "run.py", "-y"]

    sys.exit(pyinfra_main())


if __name__ == "__main__":
    main()
