"""Flutter/FVM setup."""

from pyinfra.context import host
from pyinfra.facts.files import Directory
from pyinfra.operations import files, server


def setup(user, home, enable_zsh):
    """Setup Flutter via FVM."""
    # Check if fvm is installed
    fvm_dir = host.get_fact(Directory, path=f"{home}/.fvm_flutter")

    if not fvm_dir:
        server.shell(
            name="Install FVM",
            commands=[
                "curl -fsSL https://raw.githubusercontent.com/leoafarias/fvm/"
                "refs/tags/3.2.1/scripts/install.sh | bash -s -- 3.2.1",
            ],
        )
        # Move to user home
        server.shell(
            name="Move FVM to user directory",
            commands=[
                "rm -f /usr/local/bin/fvm",
                f"mv /root/.fvm_flutter {home}/.fvm_flutter",
                f"chown -R {user}:{user} {home}/.fvm_flutter",
            ],
        )

    # Add fvm to PATH
    files.block(
        name="Add FVM to PATH in bashrc",
        path=f"{home}/.bashrc",
        content=f'export PATH="{home}/.fvm_flutter/bin:$PATH"',
        marker="# {mark} ANSIBLE MANAGED BLOCK: add fvm to PATH",
    )

    if enable_zsh:
        files.block(
            name="Add FVM to PATH in zshrc",
            path=f"{home}/.zshrc",
            content=f'export PATH="{home}/.fvm_flutter/bin:$PATH"',
            marker="# {mark} ANSIBLE ANSIBLE MANAGED BLOCK: add fvm to PATH",
        )

    # Install Android Studio snap
    server.shell(
        name="Install Android Studio snap",
        commands=["snap install android-studio --classic"],
    )

    # Add user to kvm group
    server.user(
        name="Add user to kvm group",
        user=user,
        groups=["kvm"],
    )

    # Create Dart proxy script
    files.put(
        name="Create Dart proxy script",
        dest=f"{home}/bin/dart",
        src="templates/dart-proxy.j2",
        mode="755",
    )

    # Create Flutter proxy script
    files.put(
        name="Create Flutter proxy script",
        dest=f"{home}/bin/flutter",
        src="templates/flutter-proxy.j2",
        mode="755",
    )
