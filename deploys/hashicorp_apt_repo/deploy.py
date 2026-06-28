import io

from pyinfra.facts import server as server_facts
from pyinfra.facts.files import File

from pyinfra import host
from pyinfra.operations import apt, files, server

if host.data.hashicorp_apt_repo["enabled"] or host.data.hashicorp_vault_cli["enabled"] or host.data.vagrant["enabled"]:
    keyfile = "/usr/share/keyrings/hashicorp-archive-keyring.gpg"

    server.shell(
        name="Download hashicorp gpg key",
        commands=[
            f"""keyfile={keyfile}
checksum_before="5890794459b76f45c3a25d2ecffa11477d689386bc593d1d470047f3dfef9faa91e61c1d55f89ffd6c718f8fafd181604f717b8c2dc4f374d132ae324808d54b"
if [ -f $keyfile ]; then
  checksum_before=$(shasum -a 512 $keyfile | awk '{{print $1}}')
fi
wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o $keyfile
if [ -n "$checksum_before" ]; then
  if [ ! $checksum_before = $(shasum -a 512 $keyfile | awk '{{print $1}}') ]; then
    echo "Checksum of $keyfile changed"
    exit 1
  fi
fi"""
        ],
        _sudo=True,
        _if=lambda: host.get_fact(File, keyfile) is None,
    )

    arch = "amd64"
    os_release = host.get_fact(server_facts.OsRelease)["version_codename"]

    files.put(
        name="Add hashicorp apt repository",
        src=io.StringIO(f"deb [arch={arch} signed-by={keyfile}] https://apt.releases.hashicorp.com {os_release} main"),
        dest="/etc/apt/sources.list.d/hashicorp.list",
        _sudo=True,
        mode="644",
    )

    apt.update(
        name="Update apt cache after hashicorp repo",
        _sudo=True,
    )
