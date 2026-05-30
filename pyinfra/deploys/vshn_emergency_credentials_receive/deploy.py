from pyinfra import host
from operations.github_release_binary import github_release_binary

vshn_emergency_credentials_receive = {
    # renovate: datasource=github-releases depName=vshn/emergency-credentials-receive
    "emergency_credentials_receive_version": "1.2.2",
    "checksum": "60eff914cb5e4b8771dd8606ba1b324e3183000c1a0fd91fa4ae2c82ad788afc",
    **host.data.vshn_emergency_credentials_receive,
}

if host.data.vshn_emergency_credentials_receive["enabled"]:
    github_release_binary(
        url=f"https://github.com/vshn/emergency-credentials-receive/releases/download/v{vshn_emergency_credentials_receive['emergency_credentials_receive_version']}/emergency-credentials-receive_linux_amd64",
        binary_name="emergency-credentials-receive",
        checksum=vshn_emergency_credentials_receive["checksum"],
        is_tar=False,
    )
