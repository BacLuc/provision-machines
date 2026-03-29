"""keepassxc setup."""

from pyinfra.operations import server


def setup(enable_gcr=False, socket_path=None):
    """Setup KeePassXC flatpak."""
    # Install KeePassXC via flatpak (ignore errors if flatpak not available)
    server.shell(
        name="Install KeePassXC via flatpak",
        commands=["flatpak install -y flathub org.keepassxc.KeePassXC"],
        _ignore_errors=True,
    )

    if enable_gcr and socket_path:
        # Configure SSH agent socket
        server.shell(
            name="Configure KeePassXC SSH agent",
            commands=[
                f"flatpak override org.keepassxc.KeePassXC " f"--filesystem={socket_path}",
            ],
            _ignore_errors=True,
        )
