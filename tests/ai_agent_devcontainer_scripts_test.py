import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import TypedDict, cast

ROOT = Path(__file__).parents[1]
FILES = ROOT / "deploys/development_tools/ai_agent_devcontainer/files"
START = FILES / "start-ai-agent-devcontainer.sh"
SHELL = FILES / "shell-ai-agent-devcontainer.sh"


class CommandCall(TypedDict):
    command: list[str]
    project: str | None


def project_name(workspace: Path) -> str:
    suffix = hashlib.sha256(str(workspace.resolve()).encode()).hexdigest()[:8]
    return f"ai_devcontainer_workspaces_workspace_{suffix}"


def test_persistent_workspace_keeps_existing_project_name(tmp_path: Path) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    workspace = tmp_path / "projects" / "my-repo"
    workspace.mkdir(parents=True)

    subprocess.run(
        ["bash", str(START), "--workspace-dir", str(workspace), "--down"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    compose = next(call for call in calls(log) if call["command"][:1] == ["compose"])
    assert compose["command"][2] == "ai_devcontainer_workspaces_my-repo"


def fake_commands(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "calls.jsonl"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['CALL_LOG'], 'a') as log:\n"
        "    log.write(json.dumps({'command': sys.argv[1:], 'project': os.environ.get('COMPOSE_PROJECT_NAME')}) + '\\n')\n"
        "if sys.argv[1:2] == ['ps']:\n"
        "    print('container-id')\n"
    )
    docker.chmod(0o755)
    devcontainer = bin_dir / "devcontainer"
    devcontainer.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys, time\n"
        "with open(os.environ['CALL_LOG'], 'a') as log:\n"
        "    log.write(json.dumps({'command': sys.argv[1:], 'project': os.environ.get('COMPOSE_PROJECT_NAME')}) + '\\n')\n"
        "if sys.argv[1:2] == ['up']:\n"
        "    time.sleep(30)\n"
    )
    devcontainer.chmod(0o755)
    curl = bin_dir / "curl"
    curl.write_text("#!/usr/bin/env python3\nraise SystemExit(1)\n")
    curl.chmod(0o755)
    git = bin_dir / "git"
    git.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "print({'name': 'user.name', 'email': 'user.email'}.get(sys.argv[-1], ''))\n"
    )
    git.chmod(0o755)
    return bin_dir, log


def environment(tmp_path: Path, bin_dir: Path, log: Path) -> dict[str, str]:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return {
        **os.environ,
        "HOME": str(home),
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "CALL_LOG": str(log),
        "OPENCODE_PORT": "4096",
    }


def calls(log: Path) -> list[CommandCall]:
    return [cast(CommandCall, json.loads(line)) for line in log.read_text().splitlines()]


def test_explicit_down_uses_compose_without_removing_volumes(tmp_path: Path) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    workspace = tmp_path / "checkout" / "workspace"
    workspace.mkdir(parents=True)

    subprocess.run(
        ["bash", str(START), "--workspace-dir", str(workspace), "--down"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    actual = calls(log)
    compose = next(call for call in actual if call["command"][:1] == ["compose"])
    assert compose["command"] == [
        "compose",
        "-p",
        project_name(workspace),
        "-f",
        f"{env['HOME']}/projects/provision-machines/deploys/development_tools/ai_agent_devcontainer/files/compose.yml",
        "down",
    ]
    assert "-v" not in compose["command"]
    assert "--volumes" not in compose["command"]
    assert not any(call["command"][:1] == ["up"] for call in actual)


def test_signal_cleanup_uses_same_compose_project_without_volume_removal(
    tmp_path: Path,
) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    workspace = tmp_path / "checkout" / "workspace"
    workspace.mkdir(parents=True)
    process = subprocess.Popen(
        ["bash", str(START), "--workspace-dir", str(workspace), "--no-open"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if log.exists() and any(call["command"][:1] == ["up"] for call in calls(log)):
            break
        time.sleep(0.02)
    else:
        process.kill()
        raise AssertionError("devcontainer up was not called")

    process.send_signal(signal.SIGTERM)
    process.communicate(timeout=10)

    actual = calls(log)
    up = next(call for call in actual if call["command"][:1] == ["up"])
    compose = next(call for call in actual if call["command"][:1] == ["compose"])
    assert up["project"] == project_name(workspace)
    assert compose["project"] == up["project"]
    assert compose["command"][-1] == "down"
    assert "-v" not in compose["command"]
    assert "--volumes" not in compose["command"]


def test_same_basename_workspaces_have_distinct_projects_and_helper_lookup(
    tmp_path: Path,
) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    workspaces = [tmp_path / "first" / "workspace", tmp_path / "second" / "workspace"]
    expected = []
    for workspace in workspaces:
        workspace.mkdir(parents=True)
        subprocess.run(
            ["bash", str(START), "--workspace-dir", str(workspace), "--down"],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        expected.append(project_name(workspace))

    assert expected[0] != expected[1]
    for workspace, project in zip(workspaces, expected, strict=True):
        subprocess.run(
            ["bash", str(SHELL)],
            check=True,
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
        )
        latest = calls(log)[-2]
        assert latest["command"][0] == "ps"
        assert f"label=com.docker.compose.project={project}" in latest["command"]
