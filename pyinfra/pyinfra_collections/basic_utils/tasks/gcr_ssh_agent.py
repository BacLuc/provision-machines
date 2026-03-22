"""gcr SSH agent setup."""

from pyinfra.context import host
from pyinfra.facts.files import Directory
from pyinfra.operations import apt, files


def setup(user, home, key_filename, key_comment, socket_path, enable_zsh):
    """Setup gcr-ssh-agent."""
    # Check if ssh key exists
    ssh_key_path = f"{home}/.ssh/{key_filename}"
    key_info = host.get_fact(Directory, path=ssh_key_path)

    if not key_info:
        # Install pwgen and libsecret-tools
        apt.packages(
            name="Install password generation tools",
            packages=["pwgen", "libsecret-tools"],
            update=True,
        )

    # Add gcr-ssh-agent to shell
    files.block(
        name="Add gcr-ssh-agent to bashrc",
        path=f"{home}/.bashrc",
        content=f"""export SSH_AUTH_SOCK={socket_path}

if ! ssh-add -l | grep -q "{key_comment}"; then
  ssh_key_path="$HOME/.ssh/{key_filename}"
  if [ -f "$ssh_key_path" ]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
        marker="# {mark} ANSIBLE MANAGED BLOCK: start gcr ssh agent",
    )

    if enable_zsh:
        files.block(
            name="Add gcr-ssh-agent to zshrc",
            path=f"{home}/.zshrc",
            content=f"""export SSH_AUTH_SOCK={socket_path}

if ! ssh-add -l | grep -q "{key_comment}"; then
  ssh_key_path="$HOME/.ssh/{key_filename}"
  if [ -f "$ssh_key_path" ]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
            marker="# {mark} ANSIBLE MANAGED BLOCK: start gcr ssh agent",
        )
