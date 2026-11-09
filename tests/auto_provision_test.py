import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

_DEPLOY = Path(__file__).parents[1] / "deploys" / "auto_provision"


def test_deploy_uses_jinja_templates_and_disabled_cleanup() -> None:
    deploy = (_DEPLOY / "deploy.py").read_text()

    assert "files.template(" in deploy
    assert '"enabled": False' not in deploy
    assert 'path=f"/etc/systemd/system/{filename}"' in deploy
    assert 'running=False' in deploy


def test_default_configuration_is_disabled_and_laptop_safe() -> None:
    configuration = (Path(__file__).parents[1] / "group_data" / "all.py").read_text()

    start = configuration.index("auto_provision = {")
    end = configuration.index("}\n", start) + 2
    values = configuration[start:end]
    assert '"enabled": False' in values
    assert ".local/var/auto-provision" in values
    assert '"on_calendar": "Sun *-*-* 03:00:00"' in values


def test_templates_configure_calendars_user_home_and_journald() -> None:
    service = (_DEPLOY / "files" / "auto-provision.service").read_text()
    timer = (_DEPLOY / "files" / "auto-provision.timer").read_text()
    notify_timer = (_DEPLOY / "files" / "auto-provision-notify.timer").read_text()

    assert "User={{ provision_user }}" in service
    assert "Environment=HOME={{ home }}" in service
    assert "StandardOutput=journal" in service
    assert "OnCalendar={{ on_calendar }}" in timer
    assert "OnCalendar={{ notify_on_calendar }}" in notify_timer


def test_runner_has_order_locking_and_weekly_idempotency() -> None:
    runner = (_DEPLOY / "files" / "auto-provision-runner.sh").read_text()

    assert 'flock -n 9 || exit 0' in runner
    assert '"$STATE_DIR/last-success-week"' in runner
    assert "sudo /usr/local/bin/cleanup-script" in runner
    assert '"$HOME/bin/uv" run scripts/run_pyinfra_local.py' in runner
    assert "sudo /usr/local/bin/update-script" in runner
    assert runner.index("cleanup-script") < runner.index("run_pyinfra_local.py") < runner.index("update-script")


def test_runner_stop_marks_today_and_does_not_use_dbus() -> None:
    runner = (_DEPLOY / "files" / "auto-provision-runner.sh").read_text()
    notifier = (_DEPLOY / "files" / "auto-provision-notify.sh").read_text()

    assert 'printf \'%s\\n\' "$TODAY" > "$STOP_FILE"' in runner
    assert 'if [ ! -S "$RUNTIME_DIR/bus" ]; then' in notifier
    assert "DBUS_SESSION_BUS_ADDRESS" not in notifier
    assert "sudo systemctl stop auto-provision.service" in notifier
    assert '"$STATE_DIR/stopped-today"' not in notifier
    assert "stopped-today" in notifier


def test_runner_skips_a_stopped_day() -> None:
    runner = (_DEPLOY / "files" / "auto-provision-runner.sh").read_text()

    with TemporaryDirectory() as directory:
        state = Path(directory) / "state"
        checkout = Path(directory) / "checkout" / ".git"
        state.mkdir()
        checkout.mkdir(parents=True)
        (state / "stopped-today").write_text(subprocess.check_output(["date", "+%F"], text=True).strip())
        script = runner.replace("{{ checkout_dir }}", str(checkout.parent)).replace("{{ state_dir }}", str(state))
        script = script.replace("{{ branch }}", "main")
        result = subprocess.run(["sh", "-c", script], env={**os.environ, "HOME": directory}, check=False)
        assert result.returncode == 0
