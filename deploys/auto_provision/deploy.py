import io

from pyinfra import host
from pyinfra.operations import apt, files, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

user = get_user_name()
auto_provision = host.data.auto_provision

if auto_provision["enabled"]:
    checkout_dir = auto_provision["checkout_dir"].format(user=user)
    state_dir = auto_provision["state_dir"]
    apt.packages(
        name="Install auto-provision notification dependency",
        packages=["libnotify-bin"],
        update=True,
        _sudo=True,
    )
    files.directory(
        name="Create auto-provision state directory",
        path=state_dir,
        _sudo=True,
        mode="755",
    )

    runner = open(f"{dirname_of(__file__)}/files/auto-provision-runner.sh").read()
    runner = runner.replace("@USER@", user).replace("@HOME@", f"/home/{user}")
    runner = runner.replace("@CHECKOUT_DIR@", checkout_dir)
    runner = runner.replace("@BRANCH@", auto_provision["branch"])
    runner = runner.replace("@STATE_DIR@", state_dir)
    files.put(
        name="Install auto-provision runner",
        src=io.StringIO(runner),
        dest="/usr/local/bin/auto-provision-runner",
        _sudo=True,
        mode="755",
    )

    notifier = open(f"{dirname_of(__file__)}/files/auto-provision-notify.sh").read()
    notifier = notifier.replace("@USER@", user)
    files.put(
        name="Install auto-provision notification script",
        src=io.StringIO(notifier),
        dest="/usr/local/bin/auto-provision-notify",
        _sudo=True,
        mode="755",
    )

    files.put(
        name="Install auto-provision service",
        src=io.StringIO(
            """[Unit]
Description=Provision the development machine

[Service]
Type=oneshot
ExecStart=/usr/local/bin/auto-provision-runner
StandardOutput=journal
StandardError=journal
"""
        ),
        dest="/etc/systemd/system/auto-provision.service",
        _sudo=True,
        mode="644",
    )

    files.put(
        name="Install auto-provision timer",
        src=io.StringIO(
            f"""[Unit]
Description=Schedule development machine provisioning

[Timer]
OnCalendar={auto_provision["on_calendar"]}
Persistent=true
Unit=auto-provision.service

[Install]
WantedBy=timers.target
"""
        ),
        dest="/etc/systemd/system/auto-provision.timer",
        _sudo=True,
        mode="644",
    )

    files.put(
        name="Install auto-provision notification service",
        src=io.StringIO(
            """[Unit]
Description=Notify before development machine provisioning

[Service]
Type=oneshot
ExecStart=/usr/local/bin/auto-provision-notify
StandardOutput=journal
StandardError=journal
"""
        ),
        dest="/etc/systemd/system/auto-provision-notify.service",
        _sudo=True,
        mode="644",
    )

    files.put(
        name="Install auto-provision notification timer",
        src=io.StringIO(
            f"""[Unit]
Description=Schedule the provisioning notification

[Timer]
OnCalendar={auto_provision["notify_on_calendar"]}
Persistent=false
Unit=auto-provision-notify.service

[Install]
WantedBy=timers.target
"""
        ),
        dest="/etc/systemd/system/auto-provision-notify.timer",
        _sudo=True,
        mode="644",
    )

    systemd.service(
        name="Enable auto-provision timers",
        service="auto-provision.timer",
        enabled=True,
        daemon_reload=True,
        _sudo=True,
    )
    systemd.service(
        name="Enable auto-provision notification timer",
        service="auto-provision-notify.timer",
        enabled=True,
        daemon_reload=False,
        _sudo=True,
    )
