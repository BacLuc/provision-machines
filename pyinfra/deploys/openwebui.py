from pyinfra import host
from pyinfra.operations import files, server, systemd

user = host.data.get("user", "ubuntu")

if host.data.get("enable_openwebui", False):
    
    openwebui_compose_project_dir = host.data.get("openwebui_compose_project_dir", f"/home/{user}/openwebui")
    
    server.shell(
        name="Create docker volume",
        commands=["docker volume create open-webui"],
        _sudo=True,
    )
    
    files.directory(
        name="Create compose project directory",
        path=openwebui_compose_project_dir,
        mode="755",
    )
    
    # Copy searngx directory (would need to be implemented with proper file sync)
    files.directory(
        name="Create searngx directory",
        path=f"{openwebui_compose_project_dir}/searngx",
        mode="755",
    )
    
    # Deploy docker-compose.yml (would need to be implemented with proper template)
    files.put(
        name="Deploy docker-compose.yml",
        dest=f"{openwebui_compose_project_dir}/docker-compose.yml",
        content="""version: '3'

services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "13307:8080"
    volumes:
      - open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://localhost:11434
      - WEBUI_SECRET_KEY=your-secret-key
    restart: unless-stopped

volumes:
  open-webui:
    external: true
""",
        mode="644",
    )
    
    # Deploy systemd service file
    files.put(
        name="Deploy systemd service file",
        dest="/etc/systemd/system/openwebui.service",
        content=f"""[Unit]
Description=OpenWebUI Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory={openwebui_compose_project_dir}
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
""",
        _sudo=True,
        mode="644",
    )
    
    systemd.service(
        name="Enable and start openwebui service",
        service="openwebui",
        running=True,
        enabled=True,
        restarted=True,
        _sudo=True,
    )