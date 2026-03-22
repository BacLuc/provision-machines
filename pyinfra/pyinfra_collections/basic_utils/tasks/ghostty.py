"""Ghostty removal."""

from pyinfra.operations import files, server


def remove(home):
    """Remove ghostty snap."""
    server.shell(
        name="Remove ghostty snap",
        commands=["snap remove ghostty || true"],
    )

    # Remove config directory
    files.directory(
        name="Remove ghostty config directory",
        path=f"{home}/.config/ghostty/",
        present=False,
    )
