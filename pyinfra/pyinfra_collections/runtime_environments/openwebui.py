"""OpenWebUI setup."""

import os

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import server, files


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("OpenWebUI")
def configure_openwebui(user=None, home=None, _sudo=None):
    """Configure OpenWebUI using Docker."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_openwebui", False)):
        return

    home = home or os.path.expanduser("~")
    compose_project_dir = host.data.get("openwebui_compose_project_dir", f"{home}/openwebui")

    # Create docker volume
    server.shell(
        name="Create docker volume",
        commands=["docker volume create open-webui || true"],
        _ignore_errors=True,
    )

    # Create compose project directory
    files.directory(
        name="Create compose project directory",
        path=compose_project_dir,
        present=True,
        mode="755",
    )

    # Create docker-compose.yml
    compose_content = """version: '3.8'

services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    ports:
      - "8080:8080"
    volumes:
      - open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URLS=http://host.docker.internal:11434
      - WEBUI_SECRET_KEY=
    restart: unless-stopped
"""

    files.put(
        name="Create docker-compose.yml",
        src=compose_content,
        dest=f"{compose_project_dir}/docker-compose.yml",
        mode="644",
    )

    # Start the container
    server.shell(
        name="Start OpenWebUI container",
        commands=[f"cd {compose_project_dir} && docker compose up -d"],
        _ignore_errors=True,
    )
