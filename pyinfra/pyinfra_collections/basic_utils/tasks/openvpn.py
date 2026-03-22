"""OpenVPN setup."""

from pyinfra.operations import apt


def setup():
    """Setup OpenVPN for Network Manager."""
    apt.packages(
        name="Install OpenVPN network manager packages",
        packages=["network-manager-openvpn", "network-manager-openvpn-gnome"],
        update=True,
    )
