"""SSH agent setup."""

from pyinfra.operations import files


def setup(user, home, key_filename, key_comment, enable_zsh):
    """Setup SSH agent in shell."""
    files.block(
        name="Add ssh-agent to bashrc",
        path=f"{home}/.bashrc",
        content=f"""if [ -z "$(pgrep ssh-agent)" ]; then
  rm -rf /tmp/ssh-*
  eval $(ssh-agent -s) > /dev/null
fi
export SSH_AGENT_PID=$(pgrep ssh-agent)
export SSH_AUTH_SOCK=$(find /tmp/ssh-* -name 'agent.*' | head -1)

if ! ssh-add -l | grep -q "{key_comment}"; then
  ssh_key_path="$HOME/.ssh/{key_filename}"
  if [ -f "$ssh_key_path" ]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
        marker="# {mark} ANSIBLE MANAGED BLOCK: start ssh agent",
    )

    if enable_zsh:
        files.block(
            name="Add ssh-agent to zshrc",
            path=f"{home}/.zshrc",
            content=f"""if [ -z "$(pgrep ssh-agent)" ]; then
  rm -rf /tmp/ssh-*
  eval $(ssh-agent -s) > /dev/null
fi
export SSH_AGENT_PID=$(pgrep ssh-agent)
export SSH_AUTH_SOCK=$(find /tmp/ssh-* -name 'agent.*' | head -1)

if ! ssh-add -l | grep -q "{key_comment}"; then
  ssh_key_path="$HOME/.ssh/{key_filename}"
  if [ -f "$ssh_key_path" ]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
            marker="# {mark} ANSIBLE MANAGED BLOCK: start ssh agent",
        )
