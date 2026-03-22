"""Rambox setup."""

from pyinfra.operations import server


def setup():
    """Setup Rambox snap."""
    server.shell(
        name="Install Rambox snap",
        commands=["snap install rambox"],
    )

    # Connect interfaces if needed
    server.shell(
        name="Connect rambox interfaces",
        commands=[
            "snap connect rambox:camera || true",
            "snap connect rambox:audio-record || true",
        ],
    )
