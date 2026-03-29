"""
Applications Collection

This collection contains desktop applications and utilities.
"""

from .displaylink_driver import configure_displaylink_driver
from .intellij import configure_intellij
from .okular import configure_okular
from .ubuntu_desktop import configure_ubuntu_desktop

__all__ = [
    "configure_displaylink_driver",
    "configure_intellij",
    "configure_okular",
    "configure_ubuntu_desktop",
]
