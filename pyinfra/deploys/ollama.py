from pyinfra import host
from pyinfra.operations import files, server, systemd

ollama_defaults = {
    # renovate: datasource=github-releases depName=ollama/ollama
    "ollama_version": "0.20.3",
    "model": "qwen2.5:3b",
}

ollama = ollama_defaults.copy()
if host.data.get("ollama"):
    ollama.update(host.data.get("ollama", {}))

if host.data.get("enable_ollama", False):
    
    server.shell(
        name="Install ollama",
        commands=[f"curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION={ollama['ollama_version']} sh"],
        _sudo=True,
    )
    
    files.put(
        name="Add script to update ollama",
        dest=f"{host.data.get('update_packages_script', {}).get('dir', '/usr/local/bin')}/ollama-upgrade",
        content=f"""#!/bin/sh
if [ "$(ollama --version)" != "ollama version is {ollama['ollama_version']}" ]; then
curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION={ollama['ollama_version']} sh
fi
""",
        mode="755",
        _sudo=True,
    )
    
    # Add environment variables to ollama service
    ollama_env_vars = [
        'Environment="OLLAMA_VULKAN=0"',
        'Environment="OLLAMA_CONTEXT_LENGTH=32000"',
        'Environment="OLLAMA_KEEP_ALIVE=1"',
        'Environment="OLLAMA_HOST=0.0.0.0:11434"',
    ]
    
    for env_var in ollama_env_vars:
        files.line(
            name=f"Add {env_var} to ollama service",
            path="/etc/systemd/system/ollama.service",
            line=env_var,
            regex=env_var.split('=')[0],
            _sudo=True,
        )
    
    systemd.service(
        name="Restart ollama service",
        service="ollama",
        running=True,
        restarted=True,
        enabled=True,
        _sudo=True,
    )
    
    server.shell(
        name="Pull ollama model",
        commands=[f"ollama pull {ollama['model']}"],
    )