import io

from pyinfra import host
from pyinfra.operations import apt, files, server, systemd

user = host.data.get("user", "ubuntu")

if host.data.backup_burp["enabled"]:
    backup_burp = {
        "ppa": "ppa:vshn/backup",
        "ppa_list_filename": "vshn-ubuntu-backup-noble.sources",
        "secret_store_app_name": "burp",
        "secret_store_local_pw_instance": "personal-laptop-instance",
        "secret_store_server_instance": "personal-server-laptop-server",
        **host.data.backup_burp,
    }

    server.shell(
        name="Add apt repo for burp",
        commands=[f"add-apt-repository {backup_burp['ppa']}"],
        _sudo=True,
    )

    apt.update(name="Update apt cache", _sudo=True)

    apt.packages(
        name="Install burp packages",
        packages=["burp", "libsecret-tools", "pwgen"],
        _sudo=True,
    )

    files.link(
        name="Add symlink to burp_ca",
        path="/usr/bin/burp_ca",
        target="/usr/sbin/burp_ca",
        _sudo=True,
    )

    server.shell(
        name="Fetch server backup password from store",
        commands=[f"secret-tool lookup app {backup_burp['secret_store_app_name']} instance {backup_burp['secret_store_server_instance']}"],
    )

    files.directory(
        name="Create /etc/burp directory",
        path="/etc/burp",
        _sudo=True,
        mode="775",
    )

    burp_conf = (
        "mode = client\n"
        "port = 4971\n"
        "status_port = 4972\n"
        "port_backup = 4971\n"
        "port_restore = 4973\n"
        "port_verify = 4973\n"
        "port_list = 4973\n"
        "port_delete = 4973\n"
        f"server = {backup_burp.get('backup_host', 'backup.example.com')}\n"
        f"password = {backup_burp.get('server_password', 'changeme')}\n"
        f"cname = {backup_burp.get('client_name', 'laptop')}\n"
        "protocol = 1\n"
        "pidfile = /var/run/burp.client.pid\n"
        "syslog = 0\n"
        "stdout = 1\n"
        "progress_counter = 1\n"
        "server_can_restore = 0\n"
        "cross_filesystem=/home\n"
        "cross_all_filesystems=0\n"
        "ca_burp_ca = /usr/bin/burp_ca\n"
        "ca_csr_dir = /etc/burp/CA-client\n"
        "ssl_cert_ca = /etc/burp/ssl_cert_ca.pem\n"
        "ssl_cert = /etc/burp/ssl_cert-client.pem\n"
        "ssl_key = /etc/burp/ssl_cert-client.key\n"
        f"ssl_peer_cn = {backup_burp.get('ssl_peer_cn', 'burp-server')}\n"
        "include = /home\n"
        "include = /etc\n"
        "include = /usr/local\n"
        "include = /var/local\n"
        f"exclude = '/home/{user}/VirtualBox VMs'\n"
        f"exclude = /home/{user}/NextCloud\n"
        f"exclude = /home/{user}/.vagrant.d/boxes\n"
        "exclude_fs = debugfs\n"
        "exclude_fs = devpts\n"
        "exclude_fs = devtmpfs\n"
        "exclude_fs = proc\n"
        "exclude_fs = securityfs\n"
        "exclude_fs = sysfs\n"
        "exclude_fs = tmpfs\n"
        "exclude_regex = \\.cache\n"
        "exclude_regex = \\.burpignore\n"
        "exclude_comp=bz2\n"
        "exclude_comp=gz\n"
        "exclude_comp=xz\n"
        f"encryption_password = {backup_burp.get('backup_password', 'changeme')}\n"
    )
    files.put(
        name="Configure burp",
        src=io.StringIO(burp_conf),
        dest="/etc/burp/burp.conf",
        _sudo=True,
        mode="664",
    )

    files.put(
        name="Configure burp-runner.service",
        src=io.StringIO(
            "[Unit]\n"
            "Description=Run burp command\n"
            "\n"
            "[Service]\n"
            "Type=oneshot\n"
            "ExecStart=/usr/sbin/burp -c /etc/burp/burp.conf -a t\n"
        ),
        dest="/etc/systemd/system/burp-runner.service",
        _sudo=True,
        mode="664",
    )

    files.put(
        name="Configure burp-runner.timer",
        src=io.StringIO(
            "[Unit]\n"
            "Description=Schedule burp agent\n"
            "\n"
            "[Timer]\n"
            "OnCalendar=*:0/15\n"
            "RandomizedDelaySec=10\n"
            "Persistent=false\n"
            "\n"
            "[Install]\n"
            "WantedBy=timers.target\n"
        ),
        dest="/etc/systemd/system/burp-runner.timer",
        _sudo=True,
        mode="664",
    )

    systemd.service(
        name="Enable burp-runner service",
        service="burp-runner.timer",
        running=True,
        enabled=True,
        daemon_reload=True,
        _sudo=True,
    )
