from pathlib import Path

_DEPLOY = Path(__file__).parents[1] / "deploys" / "auto_provision"


def test_runner_uses_the_provisioned_uv_binary() -> None:
    runner = (_DEPLOY / "files" / "auto-provision-runner.sh").read_text()

    assert '"$HOME/bin/uv" run scripts/run_pyinfra_local.py' in runner
    assert " && uv run scripts/run_pyinfra_local.py" not in runner


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
