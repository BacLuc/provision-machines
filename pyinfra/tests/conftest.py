"""Pytest configuration for provision-machines project."""

import sys
from pathlib import Path

# Add the project root to sys.path so tests can import shared and pyinfra_collections
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
