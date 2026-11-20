import io

from pyinfra import host
from pyinfra.facts import server as server_facts
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, server

if host.data.hashicorp_apt_repo["enabled"] or host.data.hashicorp_vault_cli["enabled"] or host.data.vagrant["enabled"]:
    keyfile = "/usr/share/keyrings/hashicorp-archive-keyring.gpg"

    server.shell(
        name="Download hashicorp gpg key",
        commands=[
            f"""keyfile={keyfile}
checksum_before="dd26ab487729e1be7656b0c8ba19db10d5a5a76fc8af80285638f8dc1b46c104c67678345a9bef1a60a88f3cd990d679c542fbd38e6ebf7a89e089b10397ebf2"
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
