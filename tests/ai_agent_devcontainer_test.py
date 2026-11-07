import os
import subprocess
from pathlib import Path

FILES = Path(__file__).parents[1] / "deploys/development_tools/ai_agent_devcontainer/files"
LAUNCHER = FILES / "start-ai-agent-devcontainer.sh"


def run_launcher(tmp_path: Path, port: str, devcontainer_exit: int = 0) -> subprocess.CompletedProcess[str]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "git").write_text('#!/bin/sh\ncase "$1" in config) echo test;; esac\n')
    (fake_bin / "openssl").write_text("#!/bin/sh\nprintf password\n")
    (fake_bin / "nc").write_text("#!/bin/sh\nexit 1\n")
    (fake_bin / "curl").write_text("#!/bin/sh\nexit 1\n")
    (fake_bin / "devcontainer").write_text(f"#!/bin/sh\nexit {devcontainer_exit}\n")
    for command in fake_bin.iterdir():
        command.chmod(0o755)
    env = os.environ | {
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "OPENCODE_PORT": port,
        "ai_agent_devcontainer_open_url": "false",
    }
    return subprocess.run([str(LAUNCHER)], cwd=tmp_path, env=env, text=True, capture_output=True, timeout=5)


def test_config_and_port_selection_are_consistent() -> None:
    dockerfile = (FILES / "Dockerfile").read_text()
    devcontainer = (FILES / "devcontainer.json").read_text()
    compose = (FILES / "compose.yml").read_text()

    assert "ENV OPENCODE_CONFIG=/home/codespace/.config/opencode/opencode.jsonc" in dockerfile
    assert "untracked-config.jsonc" in devcontainer
    assert "--port ${OPENCODE_PORT:-4096}" in devcontainer
    assert '"127.0.0.1:${OPENCODE_PORT:-4096}:${OPENCODE_PORT:-4096}"' in compose


def test_invalid_port_fails_before_startup(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "80")

    assert result.returncode != 0
    assert "valid port number" in result.stderr


def test_failed_devcontainer_up_fails_promptly(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "4096", devcontainer_exit=1)

    assert result.returncode != 0
    assert "devcontainer failed to start" in result.stderr
