import base64
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
    working_dir: str | None


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
    assert Path(env["HOME"], ".config/ai-agent-devcontainer/port_map").read_text().split()[0] == "/workspaces/my-repo"


def fake_commands(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "calls.jsonl"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['CALL_LOG'], 'a') as log:\n"
        "    log.write(json.dumps({'command': sys.argv[1:], 'project': os.environ.get('COMPOSE_PROJECT_NAME'), 'working_dir': os.environ.get('WORKING_DIR')}) + '\\n')\n"
        "if 'ps' in sys.argv and sys.argv[1] in ('ps', 'compose'):\n"
        "    if '--status' in sys.argv:\n"
        "        print('devcontainer' if os.environ.get('SERVICE_RUNNING') == '1' else '')\n"
        "    else:\n"
        "        print('container-id')\n"
    )
    docker.chmod(0o755)
    devcontainer = bin_dir / "devcontainer"
    devcontainer.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys, time\n"
        "with open(os.environ['CALL_LOG'], 'a') as log:\n"
        "    log.write(json.dumps({'command': sys.argv[1:], 'project': os.environ.get('COMPOSE_PROJECT_NAME'), 'working_dir': os.environ.get('WORKING_DIR')}) + '\\n')\n"
        "if sys.argv[1:2] == ['up']:\n"
        "    time.sleep(float(os.environ.get('UP_SLEEP', '30')))\n"
    )
    devcontainer.chmod(0o755)
    curl = bin_dir / "curl"
    curl.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['CALL_LOG'], 'a') as log:\n"
        "    log.write(json.dumps({'command': sys.argv[1:], 'project': None}) + '\\n')\n"
        "raise SystemExit(0 if os.environ.get('CURL_SUCCEEDS') == '1' else 1)\n"
    )
    nc = bin_dir / "nc"
    nc.write_text("#!/usr/bin/env bash\nexit 1\n")
    nc.chmod(0o755)
    curl.chmod(0o755)
    git = bin_dir / "git"
    git.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "print({'name': 'user.name', 'email': 'user.email'}.get(sys.argv[-1], ''))\n"
    )
    git.chmod(0o755)
    open_command = bin_dir / "open"
    open_command.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['CALL_LOG'], 'a') as log:\n"
        "    log.write(json.dumps({'command': ['open', *sys.argv[1:]], 'project': None}) + '\\n')\n"
    )
    open_command.chmod(0o755)
    return bin_dir, log


def environment(tmp_path: Path, bin_dir: Path, log: Path) -> dict[str, str]:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return {
        **os.environ,
        "HOME": str(home),
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "CALL_LOG": str(log),
        "ai_agent_devcontainer_open_url": "false",
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
    compose = next(call for call in actual if call["command"][-1:] == ["down"])
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
        ["bash", str(START), "--workspace-dir", str(workspace)],
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
    compose = next(call for call in actual if call["command"][-1:] == ["down"])
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
    ports = []
    processes = []
    for workspace in workspaces:
        workspace.mkdir(parents=True)
        processes.append(
            subprocess.Popen(
                ["bash", str(START), "--workspace-dir", str(workspace)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        )
        deadline = time.monotonic() + 5
        mapping = Path(env["HOME"], ".config/ai-agent-devcontainer/port_map")
        while time.monotonic() < deadline and (
            not mapping.exists()
            or not any(line.startswith(str(workspace) + " ") for line in mapping.read_text().splitlines())
            or not log.exists()
            or not any(
                call["command"][:1] == ["up"] and call["project"] == project_name(workspace) for call in calls(log)
            )
        ):
            time.sleep(0.01)
        assert mapping.exists()
        expected.append(project_name(workspace))
        ports.append(
            next(line.split()[1] for line in mapping.read_text().splitlines() if line.startswith(str(workspace) + " "))
        )

    assert expected[0] != expected[1]
    assert ports[0] != ports[1]
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
    for process in processes:
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=5)
    assert not Path(env["HOME"], ".config/ai-agent-devcontainer/port_map").read_text().strip()


def test_temporary_workspace_start_and_down_use_same_identity_and_remove_mapping(
    tmp_path: Path,
) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    workspace = tmp_path / "clone" / "workspace"
    workspace.mkdir(parents=True)
    env.update(OPENCODE_PORT="", SERVICE_RUNNING="1", CURL_SUCCEEDS="1", UP_SLEEP="0.05")

    process = subprocess.Popen(
        ["bash", str(START), "--workspace-dir", str(workspace)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5
    mapping = Path(env["HOME"], ".config/ai-agent-devcontainer/port_map")
    while time.monotonic() < deadline and (
        not mapping.exists() or not log.exists() or not any(call["command"][:1] == ["up"] for call in calls(log))
    ):
        time.sleep(0.01)
    project = project_name(workspace)
    port = next(line.split()[1] for line in mapping.read_text().splitlines() if line.startswith(str(workspace) + " "))
    subprocess.run(
        ["bash", str(START), "--workspace-dir", str(workspace), "--down"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )
    down = next(call for call in calls(log) if call["command"][-1:] == ["down"])
    up = next(call for call in calls(log) if call["command"][:1] == ["up"])
    readiness = next(call for call in calls(log) if call["command"][:1] == ["-s"])
    assert down["project"] == project
    assert up["working_dir"] == f"/workspaces/workspace_{hashlib.sha256(str(workspace.resolve()).encode()).hexdigest()[:8]}"
    assert base64.b64decode(readiness["command"][-1].rsplit("/", 1)[1]).decode() == up["working_dir"]
    assert not mapping.read_text().strip()
    assert port.isdigit()
    process.communicate(timeout=5)


def test_temporary_workspace_mount_matches_readiness_path_and_persistent_default() -> None:
    compose = (FILES / "compose.yml").read_text()
    assert "target: ${WORKING_DIR:-/workspaces/${WORKSPACE_BASENAME}}" in compose
    assert "working_dir: ${WORKING_DIR:-/workspaces}" in compose


def test_persistent_workspace_mount_and_working_directory_stay_at_basename(tmp_path: Path) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    workspace = tmp_path / "projects" / "my-repo"
    workspace.mkdir(parents=True)
    env.update(OPENCODE_PORT="4097", CURL_SUCCEEDS="1", SERVICE_RUNNING="1", UP_SLEEP="2")

    subprocess.run(
        ["bash", str(START), "--workspace-dir", str(workspace)],
        check=True,
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
    )

    up = next(call for call in calls(log) if call["command"][:1] == ["up"])
    assert up["working_dir"] == "/workspaces/my-repo"


def test_readiness_requires_own_running_service_and_response(tmp_path: Path) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    workspace = tmp_path / "clone" / "workspace"
    workspace.mkdir(parents=True)
    env.update(OPENCODE_PORT="4097", CURL_SUCCEEDS="1", SERVICE_RUNNING="1", UP_SLEEP="2")
    result = subprocess.run(
        ["bash", str(START), "--workspace-dir", str(workspace)],
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    ps = [call for call in calls(log) if call["command"][:2] == ["compose", "-p"] and "--status" in call["command"]]
    assert ps and all(call["project"] == project_name(workspace) for call in ps)
    subprocess.run(
        ["bash", str(START), "--workspace-dir", str(workspace), "--down"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )


def test_same_basename_temporary_workspaces_have_distinct_readiness_urls(tmp_path: Path) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    env["SERVICE_RUNNING"] = "1"
    urls: list[str] = []
    for workspace in (tmp_path / "one" / "workspace", tmp_path / "two" / "workspace"):
        workspace.mkdir(parents=True)
        process = subprocess.Popen(
            ["bash", str(START), "--workspace-dir", str(workspace)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            curl_calls = [call for call in calls(log) if call["command"][:1] == ["-s"]] if log.exists() else []
            if len(curl_calls) > len(urls):
                urls.append(curl_calls[-1]["command"][-1])
                break
            time.sleep(0.01)
        else:
            process.kill()
            raise AssertionError("readiness URL was not checked")
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=5)

    assert len(set(urls)) == 2


def test_startup_timeout_is_bounded_and_reports_project(tmp_path: Path) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    workspace = tmp_path / "clone" / "workspace"
    workspace.mkdir(parents=True)
    env.update(DEVCONTAINER_START_TIMEOUT="0", CURL_SUCCEEDS="1", SERVICE_RUNNING="")
    result = subprocess.run(
        ["bash", str(START), "--workspace-dir", str(workspace)],
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode != 0
    assert project_name(workspace) in result.stderr
    assert "Timed out waiting" in result.stderr


def test_no_open_flag_suppresses_open_while_enabled_setting_opens(tmp_path: Path) -> None:
    bin_dir, log = fake_commands(tmp_path)
    env = environment(tmp_path, bin_dir, log)
    workspace = tmp_path / "clone" / "workspace"
    workspace.mkdir(parents=True)
    env.update(
        OPENCODE_PORT="4097",
        CURL_SUCCEEDS="1",
        SERVICE_RUNNING="1",
        UP_SLEEP="0.05",
        ai_agent_devcontainer_open_url="true",
    )

    subprocess.run(
        ["bash", str(START), "--workspace-dir", str(workspace), "--no-open"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert not any(call["command"][:1] == ["open"] for call in calls(log))

    subprocess.run(
        ["bash", str(START), "--workspace-dir", str(workspace)],
        check=True,
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
    )
    opened = [call for call in calls(log) if call["command"][:1] == ["open"]]
    assert len(opened) == 1
    assert opened[0]["command"][1].startswith("http://localhost:4097/")
