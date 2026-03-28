"""Ollama/OLLAMA installation and configuration."""

import os
from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server, files, apt


@deploy("Ollama")
def configure_ollama(user=None, home=None, _sudo=None):
    """Setup Ollama for local LLM inference."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_ollama", False)):
        return

    # Install Ollama
    server.shell(
        name="Install Ollama",
        commands=["curl -fsSL https://ollama.com/install.sh | sh"],
        _ignore_errors=True,
    )

    # Create models directory
    files.directory(
        name="Create models directory",
        path="/var/ollama/models",
        present=True,
        mode="755",
    )


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)
