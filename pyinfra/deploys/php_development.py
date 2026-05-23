from pyinfra import host
from pyinfra.operations import apt, files, server

user = host.data.get("user", "ubuntu")

php_development_defaults = {
    # renovate: datasource=github-tags depName=php/php-src
    "php_version": "8.4.10",
}

php_development = php_development_defaults.copy()
if host.data.get("php_development"):
    php_development.update(host.data.get("php_development", {}))

if host.data.get("enable_php_development", False):
    
    php_version = php_development["php_version"]
    
    server.shell(
        name="Install phpenv package",
        commands=[
            "rm -rf ~/.phpenv",
            "git clone https://github.com/phpenv/phpenv.git ~/.phpenv",
        ],
    )
    
    files.block(
        name="Add phpenv to path",
        path=f"/home/{user}/.bashrc",
        marker="# PYINFRA MANAGED BLOCK: add phpenv to PATH",
        block="""export PATH="$HOME/.phpenv/bin:$PATH"
eval "$(phpenv init -)"",
    )
    
    if host.data.get("zsh", {}).get("enabled", False):
        files.block(
            name="Add phpenv to zsh",
            path=f"/home/{user}/.zshrc",
            marker="# PYINFRA MANAGED BLOCK: add phpenv to PATH",
            block="""export PATH="$HOME/.phpenv/bin:$PATH"
eval "$(phpenv init -)"",
        )
    
    files.put(
        name="Add script to update phpenv",
        dest=f"{host.data.get('update_packages_script', {}).get('dir', '/usr/local/bin')}/phpenv-upgrade",
        content=f"""#!/bin/sh
set -e

user="{user}"
phpenv_version=adc99a7

su "$user" -c "git -C /home/{user}/.phpenv fetch --tags"
su "$user" -c "git -C /home/{user}/.phpenv reset --hard $phpenv_version"
""",
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
            "libbz2-dev",
            "libcurl4-gnutls-dev",
            "libicu-dev",
            "libmcrypt-dev",
            "libonig-dev",
            "libreadline-dev",
            "libssl-dev",
            "libzip-dev",
            "libtidy-dev",
            "libxslt1-dev",
            "pkg-config",
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
        dest=f"{host.data.get('update_packages_script', {}).get('dir', '/usr/local/bin')}/phpbuild-upgrade",
        content=f"""#!/bin/sh
set -e

user="{user}"
phpbuild_version=e602902

su "$user" -c "git -C /home/{user}/.phpenv/plugins/php-build fetch --tags"
su "$user" -c "git -C /home/{user}/.phpenv/plugins/php-build reset --hard $phpbuild_version"
""",
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