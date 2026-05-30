#!/usr/bin/env -S uv run --script

import sys

from pyinfra_cli.main import main as pyinfra_main


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: run_pyinfra_single.py <deployment_script>")
        sys.exit(1)

    sys.argv = ["pyinfra", "inventory.py", sys.argv[1]]

    sys.exit(pyinfra_main())


if __name__ == "__main__":
    main()
