import os

from pyinfra import host, local
from pyinfra.facts.files import Directory
from pyinfra.operations import files, server

from operations.filesystem import DEPLOYS_DIR
from operations.user import get_user_name

if host.data.ai_agent_devcontainer["enabled"]:
    user_name = get_user_name()

    deploy_dir = str(os.path.dirname(__file__))
    files_dir = os.path.join(deploy_dir, "files")

    local.include(f"{DEPLOYS_DIR}/development_tools/devcontainer_cli/deploy.py")

    server.shell(
        name="Create ai-agent-devcontainer-home docker volume",
        commands=["docker volume create ai-agent-devcontainer-home"],
        _sudo=True,
        _if=lambda: host.get_fact(Directory, "/var/lib/docker/volumes/ai-agent-devcontainer-home") is None,
    )

    files.directory(
        name="Ensure ai-agent-devcontainer config directory exists",
        path=f"/home/{user_name}/.config/ai-agent-devcontainer",
        user=user_name,
        group=user_name,
        mode="755",
    )

    files.directory(
        name="Ensure user bin directory exists",
        path=f"/home/{user_name}/bin",
        user=user_name,
        group=user_name,
        mode="775",
    )

    files.put(
        name="Copy devcontainer script",
        src=os.path.join(files_dir, "start-ai-agent-devcontainer.sh"),
        dest=f"/home/{user_name}/bin/start-ai-agent-devcontainer",
        user=user_name,
        group=user_name,
        mode="775",
    )
