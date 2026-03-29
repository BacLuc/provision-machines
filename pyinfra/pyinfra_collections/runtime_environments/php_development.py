"""PHP development environment setup."""

import os

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations import apt, server, files, git


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("PHP Development")
def configure_php_development(user=None, home=None, _sudo=None):
    """Configure PHP development environment with phpenv."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_php_development", False)):
        return

    # Get configuration
    php_version = host.data.get("php_version", "8.4.10")
    home = home or os.path.expanduser("~")
    bin_dir = os.path.join(home, "bin")

    # Install PHP build dependencies
    apt.packages(
        name="Install PHP build dependencies",
        packages=[
            "libssl-dev",
            "libxml2-dev",
            "pkg-config",
            "libsqlite3-dev",
            "libbz2-dev",
            "libpng-dev",
            "libjpeg-dev",
            "autoconf",
            "bison",
            "build-essential",
            "ca-certificates",
            "libicu-dev",
            "libreadline-dev",
            "libzip-dev",
            "libtidy-dev",
            "libxslt1-dev",
            "re2c",
            "zlib1g-dev",
        ],
    )

    # Clone phpenv
    git.repo(
        name="Install phpenv",
        src="https://github.com/phpenv/phpenv.git",
        dest=f"{home}/.phpenv",
    )

    # Add phpenv to PATH in .bashrc
    files.line(
        name="Add phpenv to PATH in .bashrc",
        path=f"{home}/.bashrc",
        line='export PATH="$HOME/.phpenv/bin:$PATH"',
        ensure_newline=True,
    )

    files.line(
        name="Add phpenv init to .bashrc",
        path=f"{home}/.bashrc",
        line='eval "$(phpenv init -)"',
        ensure_newline=True,
    )

    # Clone php-build
    git.repo(
        name="Install php-build",
        src="https://github.com/php-build/php-build.git",
        dest=f"{home}/.phpenv/plugins/php-build",
    )

    # Install composer
    server.shell(
        name="Install composer",
        commands=[
            f"curl -s https://getcomposer.org/installer | {home}/.phpenv/versions/{php_version}/bin/php -- --install-dir={bin_dir} --filename=composer"
        ],
        _ignore_errors=True,
    )
