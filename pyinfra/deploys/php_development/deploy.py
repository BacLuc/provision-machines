import io

from pyinfra import host
from pyinfra.operations import apt, files, server

user = host.data.get("user", "ubuntu")

php_development = {
    # renovate: datasource=github-tags depName=php/php-src
    "php_version": "8.4.10",
    **host.data.php_development,
}

if host.data.php_development["enabled"]:
    php_version = php_development["php_version"]

    server.shell(
        name="Install phpenv",
        commands=[
            "rm -rf ~/.phpenv",
            "git clone https://github.com/phpenv/phpenv.git ~/.phpenv",
        ],
    )

    phpenv_path_block = (
        'export PATH="$HOME/.phpenv/bin:$PATH"\n'
        'eval "$(phpenv init -)"\n'
    )
    files.block(
        name="Add phpenv to path in bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} PYINFRA MANAGED BLOCK: add phpenv to PATH",
        content=phpenv_path_block,
    )

    if host.data.zsh["enabled"]:
        files.block(
            name="Add phpenv to path in zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: add phpenv to PATH",
            content=phpenv_path_block,
        )

    files.put(
        name="Add script to update phpenv",
        src=io.StringIO(
            "#!/bin/sh\n"
            "set -e\n"
            "\n"
            f'user="{user}"\n'
            "phpenv_version=adc99a7\n"
            "\n"
            f'su "$user" -c "git -C /home/{user}/.phpenv fetch --tags"\n'
            f'su "$user" -c "git -C /home/{user}/.phpenv reset --hard $phpenv_version"\n'
        ),
        dest=f"{host.data.update_packages_script['dir']}/phpenv-upgrade",
        mode="755",
        _sudo=True,
    )

    apt.packages(
        name="Add php build dependencies",
        packages=[
            "libssl-dev",
            "libxml2-dev",
            "pkg-config",
            "libsqlite3-dev",
            "libbz2-dev",
            "libpng-dev",
            "libjpeg-dev",
            "autoconf2.13",
            "autoconf2.64",
            "autoconf",
            "bison",
            "build-essential",
            "ca-certificates",
            "findutils",
            "libcurl4-gnutls-dev",
            "libicu-dev",
            "libmcrypt-dev",
            "libonig-dev",
            "libreadline-dev",
            "libzip-dev",
            "libtidy-dev",
            "libxslt1-dev",
            "re2c",
            "zlib1g-dev",
        ],
        install_recommends=False,
        _sudo=True,
    )

    server.shell(
        name="Add phpbuild",
        commands=[
            "rm -rf ~/.phpenv/plugins/php-build",
            "git clone https://github.com/php-build/php-build ~/.phpenv/plugins/php-build",
        ],
    )

    files.put(
        name="Add script to update phpbuild",
        src=io.StringIO(
            "#!/bin/sh\n"
            "set -e\n"
            "\n"
            f'user="{user}"\n'
            "phpbuild_version=e602902\n"
            "\n"
            f'su "$user" -c "git -C /home/{user}/.phpenv/plugins/php-build fetch --tags"\n'
            f'su "$user" -c "git -C /home/{user}/.phpenv/plugins/php-build reset --hard $phpbuild_version"\n'
        ),
        dest=f"{host.data.update_packages_script['dir']}/phpbuild-upgrade",
        mode="755",
        _sudo=True,
    )

    server.shell(
        name="Build and install php",
        commands=[
            f"/home/{user}/.phpenv/bin/phpenv install {php_version}",
            f"/home/{user}/.phpenv/bin/phpenv global {php_version}",
        ],
    )

    server.shell(
        name="Add composer",
        commands=[
            "cd /tmp",
            f"curl -s 'https://getcomposer.org/installer' | /home/{user}/.phpenv/versions/{php_version}/bin/php",
            f"mkdir -p /home/{user}/bin",
            f"mv composer.phar /home/{user}/bin/composer",
        ],
    )
