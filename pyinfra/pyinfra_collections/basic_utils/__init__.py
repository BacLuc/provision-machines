"""
Basic Utilities Collection

This collection contains core utilities and development environment setup
functionality migrated from the original Ansible basic_utils role.
"""

from .deploy import main as deploy

__all__ = ["deploy"]
