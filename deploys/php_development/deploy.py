import io

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, git, server

from operations.user import get_user_name

user = get_user_name()
php_development = host.data.php_development

if php_development["enabled"]:
    php_version = php_development["php_version"]

    git.repo(
        name="Install phpenv package",
        src="https://github.com/phpenv/phpenv.git",
        dest=f"/home/{user}/.phpenv",
        user=user,
        group=user,
    )

    phpenv_path_block = """\
export PATH="$HOME/.phpenv/bin:$PATH"
eval "$(phpenv init -)"
"""

    files.put(
        name="Add phpenv to path in bash",
        src=io.StringIO(phpenv_path_block),
        dest=f"/home/{user}/.bashrc.d/phpenv.sh",
        user=user,
        group=user,
        mode="644",
    )

    if host.data.zsh["enabled"]:
        files.put(
            name="Add phpenv to path in zsh",
            src=io.StringIO(phpenv_path_block),
            dest=f"/home/{user}/.zshrc.d/phpenv.zsh",
            user=user,
            group=user,
            mode="644",
        )

    files.put(
        name="Add script to update phpenv",
        src=io.StringIO(
            f"""#!/bin/sh
set -e

user="{user}"
phpenv_version=adc99a7

su "$user" -c "git -C /home/{user}/.phpenv fetch --tags"
su "$user" -c "git -C /home/{user}/.phpenv reset --hard $phpenv_version"
"""
        ),
        dest=f"{host.data.update_packages_script['dir']}/phpenv-upgrade",
        _sudo=True,
        mode="755",
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
        no_recommends=True,
        _sudo=True,
    )

    git.repo(
        name="Add phpbuild",
        src="https://github.com/php-build/php-build",
        dest=f"/home/{user}/.phpenv/plugins/php-build",
        user=user,
        group=user,
    )

    files.put(
        name="Add script to update phpbuild",
        src=io.StringIO(
            f"""#!/bin/sh
set -e

user="{user}"
phpbuild_version=e602902

su "$user" -c "git -C /home/{user}/.phpenv/plugins/php-build fetch --tags"
su "$user" -c "git -C /home/{user}/.phpenv/plugins/php-build reset --hard $phpbuild_version"
"""
        ),
        dest=f"{host.data.update_packages_script['dir']}/phpbuild-upgrade",
        _sudo=True,
        mode="755",
    )

    if host.get_fact(File, f"/home/{user}/.phpenv/versions/{php_version}/bin/php") is None:
        server.shell(
            name="Build and install php",
            commands=[
                f"/home/{user}/.phpenv/bin/phpenv install {php_version}",
                f"/home/{user}/.phpenv/bin/phpenv global {php_version}",
            ],
        )

    if host.get_fact(File, f"/home/{user}/bin/composer") is None:
        server.shell(
            name="Add composer",
            commands=[
                f'curl -s "https://getcomposer.org/installer" | /home/{user}/.phpenv/versions/{php_version}/bin/php',
                f"mkdir -p /home/{user}/bin",
                f"mv composer.phar /home/{user}/bin/composer",
            ],
            _chdir="/tmp",
        )
