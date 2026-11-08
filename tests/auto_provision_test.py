import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

_DEPLOY = Path(__file__).parents[1] / "deploys" / "auto_provision"


def test_runner_uses_the_provisioned_uv_binary() -> None:
    runner = (_DEPLOY / "files" / "auto-provision-runner.sh").read_text()

    assert '"$HOME/bin/uv" run scripts/run_pyinfra_local.py' in runner
    assert " && uv run scripts/run_pyinfra_local.py" not in runner


def test_notification_stop_command_records_today_as_stopped() -> None:
    notifier = (_DEPLOY / "files" / "auto-provision-notify.sh").read_text()
    deploy = (_DEPLOY / "deploy.py").read_text()

    assert "systemctl stop auto-provision.service; sudo sh -c" in notifier
    assert '.replace("@STATE_DIR@", state_dir)' in deploy

    command = notifier.split('"Run ', 1)[1].split(" to stop", 1)[0]
    command = command.replace('\\"', '"').replace("\\$", "$")
    with TemporaryDirectory() as directory:
        bin_directory = Path(directory) / "bin"
        bin_directory.mkdir()
        (bin_directory / "sudo").write_text('#!/bin/sh\nexec "$@"\n')
        (bin_directory / "systemctl").write_text("#!/bin/sh\nexit 0\n")
        for executable in (bin_directory / "sudo", bin_directory / "systemctl"):
            executable.chmod(0o755)
        state_dir = Path(directory) / "state"
        state_dir.mkdir()
        result = subprocess.run(
            ["sh", "-c", command.replace("$STATE_DIR", str(state_dir))],
            env={**os.environ, "PATH": f"{bin_directory}:{os.environ['PATH']}"},
            check=False,
        )

        assert result.returncode == 0
        assert (state_dir / "stopped-today").read_text() == subprocess.check_output(["date", "+%F"], text=True)


def test_disabling_auto_provision_removes_all_units() -> None:
    deploy = (_DEPLOY / "deploy.py").read_text()

    assert "else:\n    for service in (" in deploy
    for service in (
        "auto-provision.timer",
        "auto-provision-notify.timer",
        "auto-provision.service",
        "auto-provision-notify.service",
    ):
        assert f'        "{service}",' in deploy
        assert '            path=f"/etc/systemd/system/{service}"' in deploy


def test_notification_is_configured_two_hours_before_provisioning() -> None:
    deploy = (_DEPLOY / "deploy.py").read_text()

    assert "timedelta(hours=2)" in "".join(deploy.split())
    assert 'auto_provision["notify_on_calendar"]' in deploy
