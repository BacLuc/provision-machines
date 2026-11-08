import os
import subprocess
from pathlib import Path

FILES = Path(__file__).parents[1] / "deploys/development_tools/ai_agent_devcontainer/files"
LAUNCHER = FILES / "start-ai-agent-devcontainer.sh"


def run_launcher(
    tmp_path: Path,
    port: str,
    devcontainer_exit: int = 0,
    curl_mode: str = "fail",
    devcontainer_lifecycle: str = "running",
) -> subprocess.CompletedProcess[str]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    devcontainer_log = tmp_path / "devcontainer.log"
    (fake_bin / "git").write_text('#!/bin/sh\ncase "$1" in config) echo test;; esac\n')
    (fake_bin / "openssl").write_text("#!/bin/sh\nprintf password\n")
    (fake_bin / "nc").write_text("#!/bin/sh\nexit 1\n")
    if curl_mode == "ready":
        curl_result = (
            'printf \'%s\\n\' "$*" >> "$CURL_LOG"; '
            'case "$*" in *api/config*) printf \'{"ok":true}\';; *) printf \'{"code":"pair-code_123"}\';; esac\n'
        )
    elif curl_mode == "pair-fail":
        curl_result = 'case "$*" in *api/config*) printf \'{"ok":true}\';; *) exit 1;; esac\n'
    elif curl_mode == "pair-malformed":
        curl_result = "case \"$*\" in *api/config*) printf '{\"ok\":true}';; *) printf 'not-json';; esac\n"
    elif curl_mode == "pair-invalid-code":
        curl_result = 'case "$*" in *api/config*) printf \'{"ok":true}\';; *) printf \'{"code":"bad code"}\';; esac\n'
    else:
        curl_result = "exit 1\n"
    (fake_bin / "curl").write_text(f"#!/bin/sh\n{curl_result}")
    (fake_bin / "devcontainer").write_text(
        '#!/bin/sh\nprintf \'%s\\n\' "$1" >> "$DEVCONTAINER_LOG"\n'
        'if [ "$1" = up ]; then printf \'%s\\n\' "$$" > "$DEVCONTAINER_PID_FILE"; '
        f'if [ {devcontainer_exit} -ne 0 ]; then exit {devcontainer_exit}; fi; '
        f'if [ "{devcontainer_lifecycle}" = exits ]; then exit 0; fi; '
        f'if [ "{curl_mode}" = timeout ]; then while :; do :; done; else sleep 2; fi; fi\n'
    )
    for command in fake_bin.iterdir():
        command.chmod(0o755)
    env = os.environ | {
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "OPENCODE_PORT": port,
        "ai_agent_devcontainer_open_url": "false",
        "DEVCONTAINER_LOG": str(devcontainer_log),
        "DEVCONTAINER_PID_FILE": str(tmp_path / "devcontainer.pid"),
        "CURL_LOG": str(tmp_path / "curl.log"),
    }
    if curl_mode == "timeout":
        (fake_bin / "sleep").write_text("#!/bin/sh\nexit 0\n")
        (fake_bin / "curl").write_text("#!/bin/sh\nexit 1\n")
        (fake_bin / "sleep").chmod(0o755)
    return subprocess.run([str(LAUNCHER)], cwd=tmp_path, env=env, text=True, capture_output=True, timeout=5)


def test_invalid_port_fails_before_startup(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "80")

    assert result.returncode != 0
    assert "valid port number" in result.stderr


def test_failed_devcontainer_up_fails_promptly(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "4096", devcontainer_exit=1)

    assert result.returncode != 0
    assert "devcontainer failed to start" in result.stderr
    assert (tmp_path / "devcontainer.log").read_text().splitlines() == ["up", "down"]


def test_pairing_failure_cleans_up_devcontainer(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "4096", curl_mode="pair-fail")

    assert result.returncode != 0
    assert "could not request pairing code" in result.stderr
    assert (tmp_path / "devcontainer.log").read_text().splitlines() == ["up", "down"]


def test_authenticated_pairing_returns_code_and_keeps_devcontainer(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "4096", curl_mode="ready")

    assert result.returncode == 0
    assert result.stdout.strip().endswith("http://localhost:4096/auth/connect/pair-code_123")
    assert (tmp_path / "devcontainer.log").read_text().splitlines() == ["up"]
    assert all("-u opencode:password" in line for line in (tmp_path / "curl.log").read_text().splitlines())


def test_readiness_timeout_cleans_up_and_reaps_devcontainer(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "4096", curl_mode="timeout")

    assert result.returncode != 0
    assert "timed out waiting" in result.stderr
    assert (tmp_path / "devcontainer.log").read_text().splitlines() == ["up", "down"]
    pid = int((tmp_path / "devcontainer.pid").read_text())
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise AssertionError(f"devcontainer process {pid} is still running")


def test_completed_devcontainer_up_still_times_out_readiness(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "4096", curl_mode="timeout", devcontainer_lifecycle="exits")

    assert result.returncode != 0
    assert "timed out waiting" in result.stderr
    assert "devcontainer failed to start" not in result.stderr
    assert (tmp_path / "devcontainer.log").read_text().splitlines() == ["up", "down"]


def test_malformed_pairing_response_cleans_up_devcontainer(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "4096", curl_mode="pair-malformed")

    assert result.returncode != 0
    assert "could not extract pairing code" in result.stderr
    assert (tmp_path / "devcontainer.log").read_text().splitlines() == ["up", "down"]


def test_invalid_pairing_code_cleans_up_devcontainer(tmp_path: Path) -> None:
    result = run_launcher(tmp_path, "4096", curl_mode="pair-invalid-code")

    assert result.returncode != 0
    assert "could not extract pairing code" in result.stderr
    assert (tmp_path / "devcontainer.log").read_text().splitlines() == ["up", "down"]
