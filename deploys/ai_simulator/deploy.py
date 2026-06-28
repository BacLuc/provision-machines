import io

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, server, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

user = get_user_name()
ai_simulator = host.data.ai_simulator

if ai_simulator["enabled"]:
    port = ai_simulator.get("port", 11435)
    compose_project_dir = ai_simulator.get("compose_project_dir") or f"/home/{user}/ai-simulator"

    files.directory(
        name="Create ai-simulator compose project directory",
        path=compose_project_dir,
        user=user,
        group=user,
        mode="755",
    )

    compose_file = files.put(
        name="Deploy ai-simulator docker-compose.yml",
        src=f"{dirname_of(__file__)}/files/docker-compose.yml",
        dest=f"{compose_project_dir}/docker-compose.yml",
        user=user,
        group=user,
        mode="644",
    )

    server_file = files.put(
        name="Deploy ai-simulator server.py",
        src=f"{dirname_of(__file__)}/files/server.py",
        dest=f"{compose_project_dir}/server.py",
        user=user,
        group=user,
        mode="644",
    )

    dockerfile = files.put(
        name="Deploy ai-simulator Dockerfile",
        src=f"{dirname_of(__file__)}/files/Dockerfile",
        dest=f"{compose_project_dir}/Dockerfile",
        user=user,
        group=user,
        mode="644",
    )

    systemd_file = files.put(
        name="Deploy ai-simulator systemd service",
        src=io.StringIO(
            f"""[Unit]
Description=AI Simulator Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory={compose_project_dir}
ExecStart=/usr/bin/docker compose up -d --build
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
"""
        ),
        dest="/etc/systemd/system/ai-simulator.service",
        _sudo=True,
        mode="644",
    )

    systemd.service(
        name="Enable and start ai-simulator service",
        service="ai-simulator",
        daemon_reload=True,
        enabled=True,
        restarted=True,
        _sudo=True,
        _if=lambda: systemd_file.changed or compose_file.changed or server_file.changed or dockerfile.changed,
    )

    ufw_active = (
        host.get_fact(Command, "systemctl is-active ufw 2>/dev/null || echo inactive").strip()
        == "active"
    )

    if ufw_active:
        # UFW runs its drop rules at nftables priority 0; a custom nftables accept at
        # priority 10 fires too late and never overrides the UFW drop. Adding rules via
        # ufw itself inserts accepts inside UFW's own chain, before its default deny.
        server.shell(
            name="Allow private-network access to ai-simulator port via UFW",
            commands=[
                f"ufw allow from 127.0.0.0/8 to any port {port} proto tcp comment 'ai-simulator'",
                f"ufw allow from 10.0.0.0/8 to any port {port} proto tcp comment 'ai-simulator'",
                f"ufw allow from 172.16.0.0/12 to any port {port} proto tcp comment 'ai-simulator'",
                f"ufw allow from 192.168.0.0/16 to any port {port} proto tcp comment 'ai-simulator'",
            ],
            _sudo=True,
        )
    else:
        apt.packages(
            name="Install nftables",
            packages=["nftables"],
            _sudo=True,
        )

        files.directory(
            name="Create nftables.conf.d directory",
            path="/etc/nftables.conf.d",
            _sudo=True,
            mode="755",
        )

        nftables_ai_simulator_file = files.put(
            name="Deploy nftables configuration for ai-simulator",
            src=io.StringIO(
                f"""table inet ai_simulator_filter {{
    chain input {{
        type filter hook input priority 10; policy accept;

        tcp dport {port} ip saddr {{ 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 }} accept

        tcp dport {port} drop
    }}
}}
"""
            ),
            dest="/etc/nftables.conf.d/ai-simulator.conf",
            _sudo=True,
            mode="644",
        )

        nftables_root_file = files.block(
            name="Ensure nftables includes conf.d directory",
            path="/etc/nftables.conf",
            marker="# {mark} PYINFRA MANAGED BLOCK: include conf.d",
            content='include "/etc/nftables.conf.d/*.conf"',
            _sudo=True,
        )

        systemd.service(
            name="Ensure nftables service is enabled and running",
            service="nftables",
            daemon_reload=True,
            enabled=True,
            running=True,
            _sudo=True,
            _if=lambda: nftables_root_file.changed or nftables_ai_simulator_file.changed,
        )
