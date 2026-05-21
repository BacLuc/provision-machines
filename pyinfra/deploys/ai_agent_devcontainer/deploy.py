import os

from pyinfra import host
from pyinfra.facts.server import User
from pyinfra.operations import files, npm
from pyinfra.operations.server import shell

if host.data.ai_agent_devcontainer["enabled"]:
    """Deploy AI Agent DevContainer setup"""

    user_name = host.get_fact(User)

    deploy_dir = os.path.dirname(__file__)
    files_dir = os.path.join(deploy_dir, "files")

    shell(
        name="Check Docker availability",
        commands="command -v docker",
    )

    shell(
        name="Check Git availability",
        commands="command -v git",
    )

    shell(
        name="Check npm availability",
        commands="command -v npm",
    )

    npm.packages(
        name="Install devcontainer-cli",
        packages=["@devcontainers/cli"],
    )

    files.directory(
        name="Ensure user bin directory exists",
        path=f"/home/{user_name}/bin",
        user=user_name,
        group=user_name,
        mode="775",
    )

    # Copy start script
    files.put(
        name="Copy devcontainer script",
        src=os.path.join(files_dir, "start-ai-agent-devcontainer.sh"),
        dest=f"/home/{user_name}/bin/start-ai-agent-devcontainer",
        user=user_name,
        group=user_name,
        mode="775",
    )