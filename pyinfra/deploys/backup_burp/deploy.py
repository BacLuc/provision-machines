from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
    server,
    systemd,
)

# Get user from host data
user = host.data.get("user", "ubuntu")

if host.data.get("backup_burp", {}).get("enabled", False):
    # Set defaults for backup_burp role
    backup_burp_defaults = {
        "ppa": "ppa:vshn/backup",
        "ppa_list_filename": "vshn-ubuntu-backup-noble.sources",
        "secret_store_app_name": "burp",
        "secret_store_local_pw_instance": "personal-laptop-instance",
        "secret_store_server_instance": "personal-server-laptop-server",
    }
    
    # Combine defaults with host data
    backup_burp = backup_burp_defaults.copy()
    if host.data.get("backup_burp"):
        backup_burp.update(host.data.get("backup_burp", {}))

    # Add apt repo for burp
    server.shell(
        name="Add apt repo for burp",
        commands=[f"add-apt-repository {backup_burp['ppa']}"],
        _sudo=True,
    )

    # Update apt cache
    apt.update(
        name="Update apt cache",
        _sudo=True,
    )

    # Install burp
    apt.packages(
        name="Install burp packages",
        packages=["burp", "libsecret-tools", "pwgen"],
        _sudo=True,
    )

    # Add symlink to burp_ca
    files.link(
        name="Add symlink to burp_ca",
        path="/usr/bin/burp_ca",
        target="/usr/sbin/burp_ca",
        _sudo=True,
    )

    # Fetch server backup password from store
    server.shell(
        name="Fetch server backup password from store",
        commands=[f"secret-tool lookup app {backup_burp['secret_store_app_name']} instance {backup_burp['secret_store_server_instance']}"],
    )

    # Generate backup password if not exists
    server.shell(
        name="Generate backup password if not exists",
        commands=["pwgen 32 1"],
    )

    # Create /etc/burp dir
    files.directory(
        name="Create /etc/burp directory",
        path="/etc/burp",
        _sudo=True,
        mode="775",
    )

    # Configure burp
    files.file(
        name="Configure burp",
        path="/etc/burp/burp.conf",
        content=f"""mode = client
port = 4971
status_port = 4972
port_backup = 4971
port_restore = 4973
port_verify = 4973
port_list = 4973
port_delete = 4973
server = {backup_burp.get('backup_host', 'backup.example.com')}
password = {backup_burp.get('server_password', 'changeme')}
cname = {backup_burp.get('client_name', 'laptop')}
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
ssl_peer_cn = {backup_burp.get('ssl_peer_cn', 'burp-server')}
include = /home
include = /etc
include = /usr/local
include = /var/local
exclude = '/home/{user}/VirtualBox VMs'
exclude = /home/{user}/NextCloud
exclude = /home/{user}/.vagrant.d/boxes
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
encryption_password = {backup_burp.get('backup_password', 'changeme')}
""",
        _sudo=True,
        mode="664",
    )

    # Configure burp-runner.service
    files.file(
        name="Configure burp-runner.service",
        path="/etc/systemd/system/burp-runner.service",
        content="""[Unit]
Description=Run burp command

[Service]
Type=oneshot
ExecStart=/usr/sbin/burp -c /etc/burp/burp.conf -a t
""",
        _sudo=True,
        mode="664",
    )

    # Configure burp-runner.timer
    files.file(
        name="Configure burp-runner.timer",
        path="/etc/systemd/system/burp-runner.timer",
        content="""[Unit]
Description=Schedule burp agent

[Timer]
OnCalendar=*:0/15
RandomizedDelaySec=10
Persistent=false

[Install]
WantedBy=timers.target
""",
        _sudo=True,
        mode="664",
    )

    # Enable burp-runner service
    systemd.service(
        name="Enable burp-runner service",
        service="burp-runner.timer",
        running=True,
        enabled=True,
        daemon_reload=True,
        _sudo=True,
    )