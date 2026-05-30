import io

from pyinfra import host
from pyinfra.operations import apt, files, server
from pyinfra.facts import server as server_facts

if host.data.hashicorp_apt_repo["enabled"]:
    server.shell(
        name="Download hashicorp gpg key",
        commands=[
            "keyfile=/usr/share/keyrings/hashicorp-archive-keyring.gpg",
            'checksum_before="5890794459b76f45c3a25d2ecffa11477d689386bc593d1d470047f3dfef9faa91e61c1d55f89ffd6c718f8fafd181604f717b8c2dc4f374d132ae324808d54b"',
            "if [ -f $keyfile ]; then",
            "  checksum_before=$(shasum -a 512 $keyfile | awk '{print $1}')",
            "fi",
            "wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o $keyfile",
            'if [ -n "$checksum_before" ]; then',
            "  if [ ! $checksum_before = $(shasum -a 512 $keyfile | awk '{print $1}') ]; then",
            '    echo "Checksum of $keyfile changed"',
            "    exit 1",
            "  fi",
            "fi",
        ],
        _sudo=True,
    )

    arch = host.get_fact(server_facts.Arch)
    os_release = host.get_fact(server_facts.OsRelease).get("VERSION_CODENAME", "jammy")

    files.put(
        name="Add hashicorp apt repository",
        src=io.StringIO(
            f"deb [arch={arch} signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg]"
            f" https://apt.releases.hashicorp.com {os_release} main"
        ),
        dest="/etc/apt/sources.list.d/hashicorp.list",
        _sudo=True,
        mode="644",
    )

    apt.update(
        name="Update apt cache after hashicorp repo",
        _sudo=True,
    )
