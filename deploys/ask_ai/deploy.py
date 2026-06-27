import io

from pyinfra import host
from pyinfra.operations import files

from operations.github_release_binary import github_release_binary
from operations.user import get_user_name

user = get_user_name()
ask_ai = host.data.ask_ai

# renovate: datasource=docker depName=alpine
ALPINE_VERSION = "3.24.1"

# renovate: datasource=github-releases depName=sigoden/aichat
AICHAT_VERSION = "v0.30.0"
AICHAT_CHECKSUM = "8378dfc295093efadc3ddddd17f2b49223f120a14ef3503159f375d68f287346"

_DOCKER_CALL = f"""\
docker run --rm \\
    --user "$UID:$GID" \\
    -e XDG_CONFIG_HOME=/cfg \\
    -v "$HOME/bin/aichat:/usr/local/bin/aichat:ro" \\
    -v "$HOME/.config/aichat:/cfg/aichat:ro" \\
    "alpine:{ALPINE_VERSION}" \\
    /usr/local/bin/aichat --role '%shell%' -- "$full_prompt" \\
    | perl -0777 -pe 's/<think>.*?<\\/think>\\s*//s'\
"""

if ask_ai["enabled"]:
    github_release_binary(
        url=f"https://github.com/sigoden/aichat/releases/download/{AICHAT_VERSION}/aichat-{AICHAT_VERSION}-x86_64-unknown-linux-musl.tar.gz",
        binary_name="aichat",
        checksum=AICHAT_CHECKSUM,
    )

    # api_key goes directly into config (mode 600, never in git — set in local.py)
    aichat_config = f"""\
model: ask-ai:{ask_ai["model"]}
clients:
  - type: openai-compatible
    name: ask-ai
    api_base: {ask_ai["endpoint"]}
    api_key: "{ask_ai["api_key"]}"
    models:
      - name: {ask_ai["model"]}
        max_input_tokens: 131072
"""

    files.directory(
        name="Ensure ~/.config/aichat exists",
        path=f"/home/{user}/.config/aichat",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Deploy aichat config",
        src=io.StringIO(aichat_config),
        dest=f"/home/{user}/.config/aichat/config.yaml",
        user=user,
        group=user,
        mode="600",
    )

    if host.data.zsh["enabled"]:
        files.directory(
            name="Ensure ~/.zshrc.d exists",
            path=f"/home/{user}/.zshrc.d",
            user=user,
            group=user,
            mode="755",
        )

        # %shell% is the aichat built-in role for command-only output.
        # perl strips <think>...</think> blocks emitted by reasoning models (e.g. DeepSeek).
        # zsh history format: ": <timestamp>:<elapsed>;<command>" — strip the prefix.
        zsh_wrapper = f"""\
# ai: ask AI for a shell command and place it in the zsh readline buffer.
# Usage: ai [--history N] <prompt>
# Example: ai --history 5 find that docker command i used earlier
ai() {{
  local n_history=0
  if [[ $1 == --history ]]; then
    n_history=$2
    shift 2
  fi
  local prompt="$*"
  local full_prompt
  if (( n_history > 0 )); then
    local hist
    hist=$(tail -n "$n_history" "${{HISTFILE:-$HOME/.zsh_history}}" 2>/dev/null \\
          | sed 's/^: [0-9]*:[0-9]*;//')
    full_prompt="${{hist}}"$'\\n\\n'"Task: ${{prompt}}"
  else
    full_prompt="$prompt"
  fi
  local result
  result=$({_DOCKER_CALL}) || return 1
  print -z -- "$result"
}}
"""

        files.put(
            name="Add ai() zsh function",
            src=io.StringIO(zsh_wrapper),
            dest=f"/home/{user}/.zshrc.d/ask-ai.zsh",
            user=user,
            group=user,
            mode="644",
        )

        files.block(
            name="Source ask-ai.zsh from .zshrc",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: ask-ai",
            content=f"source /home/{user}/.zshrc.d/ask-ai.zsh",
        )

    if host.data.bash["enabled"]:
        files.directory(
            name="Ensure ~/.bashrc.d exists",
            path=f"/home/{user}/.bashrc.d",
            user=user,
            group=user,
            mode="755",
        )

        # bash has no print -z equivalent; read -re -i pre-fills readline with the result.
        # The user edits the command and presses Enter to run, or Ctrl-C to abort.
        # bash history format: plain lines, no timestamp prefix.
        bash_wrapper = f"""\
# ai: ask AI for a shell command, open it in readline for editing, then run it.
# Usage: ai [--history N] <prompt>
# Example: ai --history 5 find that docker command i used earlier
ai() {{
  local n_history=0
  if [[ "$1" == --history ]]; then
    n_history="$2"
    shift 2
  fi
  local prompt="$*"
  local full_prompt
  if (( n_history > 0 )); then
    local hist
    hist=$(tail -n "$n_history" "${{HISTFILE:-$HOME/.bash_history}}" 2>/dev/null)
    full_prompt="${{hist}}"$'\\n\\n'"Task: ${{prompt}}"
  else
    full_prompt="$prompt"
  fi
  local result
  result=$({_DOCKER_CALL}) || return 1
  local cmd
  IFS= read -re -i "$result" cmd || return 0
  [[ -n "$cmd" ]] || return 0
  history -s -- "$cmd"
  eval "$cmd"
}}
"""

        files.put(
            name="Add ai() bash function",
            src=io.StringIO(bash_wrapper),
            dest=f"/home/{user}/.bashrc.d/ask-ai.sh",
            user=user,
            group=user,
            mode="644",
        )

        files.block(
            name="Source ask-ai.sh from .bashrc",
            path=f"/home/{user}/.bashrc",
            marker="# {mark} PYINFRA MANAGED BLOCK: ask-ai",
            content=f"source /home/{user}/.bashrc.d/ask-ai.sh",
        )
