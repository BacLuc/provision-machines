import io

from pyinfra import host
from pyinfra.operations import files, server, systemd

ollama = {
    # renovate: datasource=github-releases depName=ollama/ollama
    "ollama_version": "0.20.3",
    "model": "qwen2.5:3b",
    **host.data.ollama,
}

if host.data.ollama["enabled"]:
    server.shell(
        name="Install ollama",
        commands=[f"curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION={ollama['ollama_version']} sh"],
        _sudo=True,
    )

    files.put(
        name="Add script to update ollama",
        src=io.StringIO(
            "#!/bin/sh\n"
            f"if [ \"$(ollama --version)\" != \"ollama version is {ollama['ollama_version']}\" ]; then\n"
            f"curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION={ollama['ollama_version']} sh\n"
            "fi\n"
        ),
        dest=f"{host.data.update_packages_script['dir']}/ollama-upgrade",
        mode="755",
        _sudo=True,
    )

    for env_var in [
        'Environment="OLLAMA_VULKAN=0"',
        'Environment="OLLAMA_CONTEXT_LENGTH=32000"',
        'Environment="OLLAMA_KEEP_ALIVE=1"',
        'Environment="OLLAMA_HOST=0.0.0.0:11434"',
    ]:
        files.line(
            name=f"Add {env_var} to ollama service",
            path="/etc/systemd/system/ollama.service",
            line=env_var,
            replace=env_var.split('=')[0],
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
