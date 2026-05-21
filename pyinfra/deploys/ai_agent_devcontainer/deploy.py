import os
import sys
from pyinfra import host
from pyinfra.operations import files, npm, server
from pyinfra.facts.server import User

# Add current directory to sys.path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    default_opencode_port,
    opencode_version,
    devcontainer_image_version,
    nvm_version,
    node_version,
    systemctl_version,
)


def deploy_ai_agent_devcontainer():
    """Deploy AI Agent DevContainer setup"""
    
    # Get user information
    user_name = host.get_fact(User)
    
    # Define file paths
    deploy_dir = os.path.dirname(__file__)
    files_dir = os.path.join(deploy_dir, "files")
    
    # Prerequisite checks
    server.shell(
        name="Check Docker availability",
        commands="command -v docker",
        error_on_fail=True,
    )
    
    server.shell(
        name="Check Git availability",
        commands="command -v git",
        error_on_fail=True,
    )
    
    # Make sure npm is available to install devcontainer-cli
    server.shell(
        name="Check npm availability",
        commands="command -v npm",
        error_on_fail=True,
    )

    # Install devcontainer-cli dependency
    npm.packages(
        name="Install devcontainer-cli",
        packages=["@devcontainers/cli"],
        global_=True,
        _sudo=True,
    )
    
    # Create user bin directory
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
    
    # Create opencode config directory
    files.directory(
        name="Create opencode config directory",
        path=f"/home/{user_name}/.config/opencode",
        user=user_name,
        group=user_name,
        mode="755",
    )
    
    # Sync opencode configuration files
    files.sync(
        name="Sync opencode configuration",
        src=os.path.join(files_dir, "opencode"),
        dest=f"/home/{user_name}/.config/opencode",
        user=user_name,
        group=user_name,
        delete=True,
    )
    
    # Create devcontainer files directory
    devcontainer_dest = f"/home/{user_name}/.config/devcontainer/ai_agent_devcontainer"
    files.directory(
        name="Create devcontainer files directory",
        path=devcontainer_dest,
        user=user_name,
        group=user_name,
        mode="755",
    )
    
    # Copy devcontainer configuration files
    for filename in ["devcontainer.json", "compose.yml", "Dockerfile"]:
        if os.path.exists(os.path.join(files_dir, filename)):
            files.put(
                name=f"Copy {filename}",
                src=os.path.join(files_dir, filename),
                dest=os.path.join(devcontainer_dest, filename),
                user=user_name,
                group=user_name,
                mode="644",
            )

# Check if ai_agent_devcontainer is enabled
if host.data.get("ai_agent_devcontainer", {}).get("enabled", False):
    deploy_ai_agent_devcontainer()