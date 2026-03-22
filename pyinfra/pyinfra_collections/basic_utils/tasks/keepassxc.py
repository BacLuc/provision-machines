"""keepassxc setup."""

from pyinfra.operations import server


def setup(enable_gcr=False, socket_path=None):
    """Setup KeePassXC flatpak."""
    # Install KeePassXC via flatpak
    server.shell(
        name="Install KeePassXC via flatpak",
        commands=["flatpak install -y flathub org.keepassxc.KeePassXC"],
    )

    if enable_gcr and socket_path:
        # Configure SSH agent socket
        server.shell(
            name="Configure KeePassXC SSH agent",
            commands=[
                f"flatpak override org.keepassxc.KeePassXC " f"--filesystem={socket_path}",
            ],
        )
