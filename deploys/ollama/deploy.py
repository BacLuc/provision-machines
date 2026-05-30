import io

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, server, systemd

from operations.user import get_user_name

user = get_user_name()
ollama = host.data.ollama

if ollama["enabled"]:
    model = ollama["model"]
    model_mmap_dest = f"/var/ollama/models/{model.replace(':', '_')}-mmap"

    server.shell(
        name="Install ollama",
        commands=[f"curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION={ollama['ollama_version']} sh"],
        _sudo=True,
        _if=lambda: host.get_fact(File, "/usr/local/bin/ollama") is None,
    )

    files.put(
        name="Add script to update ollama",
        src=io.StringIO(
            f"""if [ "$(ollama --version)" != "ollama version is {ollama["ollama_version"]}" ]; then
curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION={ollama["ollama_version"]} sh
fi
"""
        ),
        dest=f"{host.data.update_packages_script['dir']}/ollama-upgrade",
        _sudo=True,
        mode="755",
    )

    service_exists = host.get_fact(File, "/etc/systemd/system/ollama.service") is not None
    if service_exists:
        ollama_service = files.block(
            name="Add ollama environment variables",
            path="/etc/systemd/system/ollama.service",
            marker="# {mark} PYINFRA MANAGED BLOCK: ollama environment",
            line='^Environment="PATH=',
            after=True,
            content="""Environment="OLLAMA_VULKAN=0"
Environment="OLLAMA_CONTEXT_LENGTH=32000"
Environment="OLLAMA_KEEP_ALIVE=1"
Environment="OLLAMA_HOST=0.0.0.0:11434\"""",
            _sudo=True,
        )

        systemd.service(
            name="Daemon-reload and restart ollama service",
            service="ollama.service",
            daemon_reload=True,
            restarted=True,
            _sudo=True,
            _if=lambda: ollama_service.changed,
        )

        files.directory(
            name="Create models directory",
            path="/var/ollama/models",
            user=user,
            group=user,
            _sudo=True,
            mode="755",
        )

        model_mmap_file = files.put(
            name="Create a model to map fully into ram",
            src=io.StringIO(f"""\
FROM {model}
PARAMETER use_mmap false
"""),
            dest=model_mmap_dest,
            mode="755",
        )

        server.shell(
            name="Create model from file",
            commands=[f"ollama create {model}-mmap -f {model_mmap_dest}"],
            _if=lambda: model_mmap_file.changed,
        )

        server.shell(
            name="Run the model",
            commands=[f"ollama run {model}-mmap"],
            _if=lambda: model_mmap_file.changed,
        )

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

    nftables_ollama_file = files.put(
        name="Deploy nftables configuration for ollama to conf.d",
        src=io.StringIO(
            """table inet ollama_filter {
    chain input {
        type filter hook input priority 10; policy accept;

        iif "lo" tcp dport 11434 accept

        iifname "docker*" tcp dport 11434 accept
        iifname "br-*" tcp dport 11434 accept

        tcp dport 11434 drop
    }
}
"""
        ),
        dest="/etc/nftables.conf.d/ollama.conf",
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
        _if=lambda: nftables_root_file.changed or nftables_ollama_file.changed,
    )
