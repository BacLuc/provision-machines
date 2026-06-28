import io

from pyinfra.facts.files import File
from pyinfra.facts.server import Command

from operations.user import get_user_name
from pyinfra import host
from pyinfra.operations import apt, files, server, systemd

user = get_user_name()
backup_burp = host.data.backup_burp

if backup_burp["enabled"]:
    app_name = backup_burp["secret_store_app_name"]
    server_instance = backup_burp["secret_store_server_instance"]
    local_pw_instance = backup_burp["secret_store_local_pw_instance"]

    server.shell(
        name="Add apt repo for burp",
        commands=[f"add-apt-repository -y {backup_burp['ppa']}"],
        _sudo=True,
        _if=lambda: host.get_fact(File, f"/etc/apt/sources.list.d/{backup_burp['ppa_list_filename']}") is None,
    )

    apt.packages(
        name="Install burp",
        packages=["burp", "libsecret-tools", "pwgen"],
        update=True,
        _sudo=True,
    )

    files.link(
        name="Add symlink to burp_ca",
        path="/usr/bin/burp_ca",
        target="/usr/sbin/burp_ca",
        _sudo=True,
    )

    server_pw = host.get_fact(Command, f"secret-tool lookup app {app_name} instance {server_instance} || true").strip()
    if len(server_pw) <= 12:
        raise ValueError(
            f"Please add the server password with: "
            f'secret-tool store --label="Burp server password" app {app_name} instance {server_instance}'
        )

    backup_pw = host.get_fact(
        Command, f"secret-tool lookup app {app_name} instance {local_pw_instance} || true"
    ).strip()
    if not backup_pw:
        backup_pw = host.get_fact(Command, "pwgen 32 1").strip()
        server.shell(
            name="Store backup password in secret store",
            commands=[f'secret-tool store --label="Burp local password" app {app_name} instance {local_pw_instance}'],
            _stdin=backup_pw,
        )

    files.directory(
        name="Create /etc/burp dir",
        path="/etc/burp",
        _sudo=True,
        mode="754",
    )

    excludes = "\n".join(f"exclude = {exclude}" for exclude in backup_burp.get("excludes", []))
    burp_conf = f"""mode = client
port = 4971
status_port = 4972
port_backup = 4971
port_restore = 4973
port_verify = 4973
port_list = 4973
port_delete = 4973
server = {backup_burp["backup_host"]}
password = {server_pw}
cname = {backup_burp["client_name"]}
protocol = 1
pidfile = /var/run/burp.client.pid
syslog = 0
stdout = 1
progress_counter = 1
server_can_restore = 0
cross_filesystem=/home
cross_all_filesystems=0
ca_burp_ca = /usr/bin/burp_ca
ca_csr_dir = /etc/burp/CA-client
ssl_cert_ca = /etc/burp/ssl_cert_ca.pem
ssl_cert = /etc/burp/ssl_cert-client.pem
ssl_key = /etc/burp/ssl_cert-client.key
ssl_peer_cn = {backup_burp["ssl_peer_cn"]}
include = /home
include = /etc
include = /usr/local
include = /var/local
exclude = '/home/{user}/VirtualBox VMs'
exclude = /home/{user}/NextCloud
exclude = /home/{user}/.vagrant.d/boxes
{excludes}
exclude_fs = debugfs
exclude_fs = devpts
exclude_fs = devtmpfs
exclude_fs = proc
exclude_fs = securityfs
exclude_fs = sysfs
exclude_fs = tmpfs
exclude_regex = \\.cache
exclude_regex = \\.burpignore
exclude_comp=bz2
exclude_comp=gz
exclude_comp=xz
encryption_password = {backup_pw}
"""
    files.put(
        name="Configure burp",
        src=io.StringIO(burp_conf),
        dest="/etc/burp/burp.conf",
        _sudo=True,
        mode="640",
    )

    files.put(
        name="Configure burp-runner.service",
        src=io.StringIO(
            """[Unit]
Description=Run burp command

[Service]
Type=oneshot
ExecStart=/usr/sbin/burp -c /etc/burp/burp.conf -a t
"""
        ),
        dest="/etc/systemd/system/burp-runner.service",
        _sudo=True,
        mode="640",
    )

    files.put(
        name="Configure burp-runner.timer",
        src=io.StringIO(
            """[Unit]
Description=Schedule burp agent

[Timer]
OnCalendar=*:0/15
RandomizedDelaySec=10
Persistent=false

[Install]
WantedBy=timers.target
"""
        ),
        dest="/etc/systemd/system/burp-runner.timer",
        _sudo=True,
        mode="640",
    )

    systemd.service(
        name="Enable burp-runner timer",
        service="burp-runner.timer",
        enabled=True,
        daemon_reload=True,
        _sudo=True,
    )
