"""
Shared Operations for Pyinfra Collections

This package contains common operations that can be reused across collections.
"""

from .install_github_binary import get_github_release_info, install_github_binary

__all__ = ["install_github_binary", "get_github_release_info"]
