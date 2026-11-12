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
    assert '"ci_environment": ""' in values
    assert ".local/var/auto-provision" in values
    assert '"on_calendar": "Sun *-*-* 03:00:00"' in values

    ci_configuration = (Path(__file__).parents[1] / "group_data" / "ci.py").read_text()
    ci_start = ci_configuration.index("auto_provision = {")
    ci_end = ci_configuration.index("}\n", ci_start) + 2
    ci_values = ci_configuration[ci_start:ci_end]
    assert '"ci_environment": "true"' in ci_values


def test_templates_configure_calendars_user_home_without_redundant_journald() -> None:
    service = (_DEPLOY / "files" / "auto-provision.service").read_text()
    notify_service = (_DEPLOY / "files" / "auto-provision-notify.service").read_text()
    timer = (_DEPLOY / "files" / "auto-provision.timer").read_text()
    notify_timer = (_DEPLOY / "files" / "auto-provision-notify.timer").read_text()

    assert "User={{ provision_user }}" in service
    assert "Environment=HOME={{ home }}" in service
    assert "Environment=CI={{ ci_environment }}" in service
    assert "StandardOutput=journal" not in service
    assert "StandardError=journal" not in service
    assert "StandardOutput=journal" not in notify_service
    assert "StandardError=journal" not in notify_service
    assert "OnCalendar={{ on_calendar }}" in timer
    assert "OnCalendar={{ notify_on_calendar }}" in notify_timer


def test_runner_has_order_locking_and_weekly_idempotency() -> None:
    runner = (_DEPLOY / "files" / "auto-provision-runner.sh").read_text()

    assert 'flock -n 9 || exit 0' in runner
    assert '"$STATE_DIR/last-success-week"' in runner
    assert "sudo /usr/local/bin/cleanup-script" in runner
    assert '"$HOME/bin/uv" run scripts/run_pyinfra_local.py' in runner
    assert "sudo /usr/local/bin/update-script" in runner
    assert 'if [ "${CI:-}" != "true" ]; then' in runner
    assert 'export XDG_RUNTIME_DIR="/run/user/$(id -u)"' in runner
    assert runner.index('if [ "${CI:-}" != "true" ]; then') < runner.index("cleanup-script")
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


def test_runner_skips_git_sync_in_ci_and_runs_it_outside() -> None:
    runner = (_DEPLOY / "files" / "auto-provision-runner.sh").read_text()

    with TemporaryDirectory() as directory:
        stubs = Path(directory) / "stubs"
        home = Path(directory) / "home"
        stubs.mkdir()
        home.mkdir()
        (stubs / "git").write_text("#!/bin/sh\nexit 42\n")
        (stubs / "sudo").write_text("#!/bin/sh\nexit 0\n")
        (home / "bin").mkdir()
        (home / "bin" / "uv").write_text("#!/bin/sh\nexit 0\n")
        for stub in (stubs / "git", stubs / "sudo", home / "bin" / "uv"):
            stub.chmod(0o755)
        script = runner.replace("{{ branch }}", "main")
        env = {**os.environ, "HOME": str(home), "PATH": f"{stubs}:{os.environ['PATH']}"}

        ci_state = Path(directory) / "ci-state"
        ci_checkout = Path(directory) / "ci-checkout" / ".git"
        ci_state.mkdir()
        ci_checkout.mkdir(parents=True)
        ci_script = script.replace("{{ checkout_dir }}", str(ci_checkout.parent)).replace("{{ state_dir }}", str(ci_state))
        result = subprocess.run(["sh", "-c", ci_script], env={**env, "CI": "true"}, check=False)
        assert result.returncode == 0
        assert (ci_state / "last-success-week").read_text().strip() == subprocess.check_output(["date", "+%G-%V"], text=True).strip()

        local_state = Path(directory) / "local-state"
        local_checkout = Path(directory) / "local-checkout" / ".git"
        local_state.mkdir()
        local_checkout.mkdir(parents=True)
        local_script = script.replace("{{ checkout_dir }}", str(local_checkout.parent)).replace("{{ state_dir }}", str(local_state))
        result = subprocess.run(["sh", "-c", local_script], env={k: v for k, v in env.items() if k != "CI"}, check=False)
        assert result.returncode == 42
