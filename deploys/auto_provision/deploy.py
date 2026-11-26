from pyinfra import host
from pyinfra.operations import apt, files, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

user = get_user_name()
auto_provision = host.data.auto_provision
service_files = (
    "auto-provision.service",
    "auto-provision.timer",
    "auto-provision-notify.service",
    "auto-provision-notify.timer",
)

if auto_provision["enabled"]:
    home = f"/home/{user}"
    context = {
        **auto_provision,
        "provision_user": user,
        "home": home,
        "state_dir": auto_provision["state_dir"].format(user=user),
        "checkout_dir": auto_provision["checkout_dir"].format(user=user),
    }
    apt.packages(
        name="Install auto-provision notification dependency",
        packages=["libnotify-bin"],
        update=True,
        _sudo=True,
    )
    files.directory(
        name="Create auto-provision state directory",
        path=context["state_dir"],
        user=user,
        group=user,
        mode="755",
    )
    for filename in ("auto-provision-runner.sh", "auto-provision-notify.sh"):
        files.template(
            name=f"Install {filename}",
            src=f"{dirname_of(__file__)}/files/{filename}",
            dest=f"/usr/local/bin/{filename[:-3]}",
            **context,
            _sudo=True,
            mode="755",
        )
    for filename in service_files:
        files.template(
            name=f"Install {filename}",
            src=f"{dirname_of(__file__)}/files/{filename}",
            dest=f"/etc/systemd/system/{filename}",
            **context,
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
        _sudo=True,
    )
else:
    for filename in service_files:
        systemd.service(
            name=f"Disable {filename}",
            service=filename,
            enabled=False,
            running=False,
            daemon_reload=filename == service_files[0],
            _sudo=True,
        )
        files.file(
            name=f"Remove {filename}",
            path=f"/etc/systemd/system/{filename}",
            present=False,
            _sudo=True,
        )
