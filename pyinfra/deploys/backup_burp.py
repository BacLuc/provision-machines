from pyinfra import host
from pyinfra.operations import apt, files, server

backup_burp_defaults = {
    "ppa": "ppa:vshn/backup",
    "ppa_list_filename": "vshn-ubuntu-backup-noble.sources",
    "secret_store_app_name": "burp",
    "secret_store_local_pw_instance": "personal-laptop-instance",
    "secret_store_server_instance": "personal-server-laptop-server",
}

backup_burp = backup_burp_defaults.copy()
if host.data.get("backup_burp"):
    backup_burp.update(host.data.get("backup_burp", {}))

if host.data.get("enable_backup_burp", False):
    
    server.shell(
        name="Add apt repo for burp",
        commands=[f"add-apt-repository {backup_burp['ppa']}"],
        _sudo=True,
    )
    
    apt.update(
        name="Update apt cache",
        _sudo=True,
    )
    
    apt.packages(
        name="Install burp",
        packages=["burp", "libsecret-tools", "pwgen"],
        _sudo=True,
    )
    
    files.link(
        name="Add symlink to burp_ca",
        src="/usr/sbin/burp_ca",
        dest="/usr/bin/burp_ca",
        _sudo=True,
    )
    
    # Simplified password handling - would need proper secret-tool integration
    server.shell(
        name="Fetch server backup password from store",
        commands=[f"secret-tool lookup app {backup_burp['secret_store_app_name']} instance {backup_burp['secret_store_server_instance']}"],
        ignore_errors=True,
    )
    
    server.shell(
        name="Fetch backup password from store",
        commands=[f"secret-tool lookup app {backup_burp['secret_store_app_name']} instance {backup_burp['secret_store_local_pw_instance']}"],
        ignore_errors=True,
    )
    
    files.directory(
        name="Create /etc/burp dir",
        path="/etc/burp",
        _sudo=True,
        mode="775",
    )
    
    # Simplified burp configuration - would need proper template
    files.put(
        name="Configure burp",
        dest="/etc/burp/burp.conf",
        content=f"""mode = client
port = 4971
status_port = 4972
port_backup = 4971
port_restore = 4973
port_verify = 4973
port_list = 4973
port_delete = 4973
server = {backup_burp.get('backup_host', 'backup.example.com')}
password = {backup_burp.get('server_pw', 'your_password_here')}
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
ssl_peer_cn = {backup_burp.get('ssl_peer_cn', 'backup.example.com')}
""",
        _sudo=True,
        mode="644",
    )