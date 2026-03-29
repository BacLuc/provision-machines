"""Burp backup client setup."""

import os
from io import StringIO

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, server, files


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Burp Backup")
def configure_backup_burp(user=None, home=None, _sudo=None):
    """Configure Burp backup client."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_backup_burp", False)):
        return

    # Add VSHN PPA
    server.shell(
        name="Add VSHN backup PPA",
        commands=["add-apt-repository ppa:vshn/backup -y"],
        _ignore_errors=True,
    )

    # Update apt cache
    apt.update(
        name="Update apt cache",
    )

    # Install burp and dependencies
    apt.packages(
        name="Install burp and dependencies",
        packages=["burp", "libsecret-tools", "pwgen"],
    )

    # Add symlink to burp_ca
    server.shell(
        name="Add symlink to burp_ca",
        commands=["ln -sf /usr/sbin/burp_ca /usr/bin/burp_ca"],
        _ignore_errors=True,
    )

    # Create /etc/burp dir
    files.directory(
        name="Create /etc/burp directory",
        path="/etc/burp",
        present=True,
        mode="750",
    )

    # Create burp.conf
    home = home or os.path.expanduser("~")
    backup_host = host.data.get("backup_host", "backup.example.com")
    client_name = host.data.get("client_name", "client")

    burp_conf = f"""mode = client
port = 4971
status_port = 4972
port_backup = 4971
port_restore = 4973
port_verify = 4973
port_list = 4973
port_delete = 4973
server = {backup_host}
password = CHANGE_ME
cname = {client_name}
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
ssl_peer_cn = {backup_host}
include = /home
include = /etc
include = /usr/local
include = /var/local
exclude_regex = \\.cache
exclude_regex = \\.burpignore
exclude_comp=bz2
exclude_comp=gz
exclude_comp=xz
encryption_password = CHANGE_ME
"""

    files.put(
        name="Create burp.conf",
        src=StringIO(burp_conf),
        dest="/etc/burp/burp.conf",
        mode="640",
    )
