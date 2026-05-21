from pyinfra import host
from pyinfra.operations import apt
from pyinfra.operations.server import shell

if host.data.basicsetup["enabled"]:
    basic_tools = host.data.basicsetup["basic_tools"]
    additional_tools = host.data.basicsetup["additional_tools"]
    timezone = host.data.basicsetup["timezone"]
    locale = host.data.basicsetup["locale"]

    apt.packages(
        name="Install basic tools",
        packages=basic_tools,
        update=True,
        _sudo=True,
    )

    apt.packages(
        name="Install additional tools",
        packages=additional_tools,
        _sudo=True,
    )

    shell(
        name=f"Set timezone to {timezone}",
        commands=[
            f"ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime",
            f"echo '{timezone}' > /etc/timezone",
        ],
        _sudo=True,
    )

    shell(
        name=f"Set locale to {locale}",
        commands=[
            f"update-locale LANG={locale}",
            f"locale-gen {locale}",
        ],
        _sudo=True,
    )
