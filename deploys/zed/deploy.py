import io
import json

from pyinfra import host
from pyinfra.facts.files import Directory, File, Link
from pyinfra.facts.server import Command
from pyinfra.operations import files, flatpak, server

from operations.homebrew import HOMEBREW_CELLAR, user_brew_bin
from operations.user import get_user_name

user = get_user_name()
zed = host.data.zed

flatpak.packages(
    name="Remove zed flatpak",
    packages=["dev.zed.Zed"],
    present=False,
)

if zed["enabled"]:
    zed_version = "v0.204.5"
    # renovate: datasource=github-releases depName=zed-industries/delta-nix
    delta_version = "0.19.2"

    zed_config = {
        "language_models": {
            "openai_compatible": {
                "cortecs": {
                    "api_url": "https://api.cortecs.ai/v1/",
                    "available_models": [
                        {
                            "name": name,
                            "max_tokens": 200000,
                            "max_output_tokens": 32000,
                            "max_completion_tokens": 200000,
                            "capabilities": {
                                "tools": True,
                                "images": False,
                                "parallel_tool_calls": name == "claude-opus4-5",
                                "prompt_cache_key": False,
                                "chat_completions": True,
                            },
                        }
                        for name in [
                            "devstral-2512",
                            "gpt-oss-120b",
                            "claude-opus4-5",
                            "qwen3-next-80b-a3b-thinking",
                            "kimi-k2-thinking",
                            "qwen3-coder-30b-a3b-instruct",
                        ]
                    ],
                },
            },
        },
        "agent": {
            "default_model": {"provider": "ollama", "model": "mistral:7b-mmap"},
        },
        "features": {"edit_prediction_provider": "none"},
        "auto_install_extensions": {
            "ansible": True,
            "docker-compose": True,
            "dockerfile": True,
            "helm": True,
            "yaml": True,
            "html": True,
        },
        "autosave": {"after_delay": {"milliseconds": 100}},
        "base_keymap": "JetBrains",
        "buffer_font_size": 16,
        "drag_and_drop_selection": {"enabled": False},
        "edit_predictions": {
            "mode": "subtle",
            "copilot": {"proxy": None, "proxy_no_verify": None, "enterprise_uri": None},
            "enabled_in_text_threads": False,
        },
        "file_types": {
            "Ansible": [
                "**.ansible.yml",
                "**.ansible.yaml",
                "**/defaults/*.yml",
                "**/defaults/*.yaml",
                "**/meta/*.yml",
                "**/meta/*.yaml",
                "**/tasks/*.yml",
                "**/tasks/*.yaml",
                "**/handlers/*.yml",
                "**/handlers/*.yaml",
                "**/group_vars/*.yml",
                "**/group_vars/*.yaml",
                "**/playbooks/*.yaml",
                "**/playbooks/*.yml",
                "**playbook*.yaml",
                "**playbook*.yml",
            ],
            "Helm": [
                "**/templates/**/*.tpl",
                "**/templates/**/*.yaml",
                "**/templates/**/*.yml",
                "**/helmfile.d/**/*.yaml",
                "**/helmfile.d/**/*.yml",
                "**/values*.yaml",
            ],
        },
        "languages": {"YAML": {"format_on_save": "off"}},
        "lsp": {
            "helm_ls": {
                "settings": {
                    "yamlls": {
                        "path": f"/home/{user}/.local/share/zed/languages/yaml-language-server/node_modules/.bin/yaml-language-server",
                    },
                },
            },
            "yaml-language-server": {
                "enabled": False,
                "settings": {"yaml": {"format": {"singleQuote": True}}},
            },
        },
        "restore_on_startup": "none",
        "show_edit_predictions": True,
        "telemetry": {"metrics": False, "diagnostics": False},
        "theme": {"mode": "system", "light": "One Dark", "dark": "One Dark"},
        "ui_font_size": 16,
    }

    zed_keymap = [{"context": "Editor", "bindings": {"ctrl-k": None}}]

    zed_tasks = [
        {"label": "Cherry-Pick", "command": "git", "args": ["cherry-pick", "$ZED_GIT_SHA"], "tags": ["git-command"]},
        {
            "label": "Create Branch from Here",
            "command": "bash",
            "args": [
                "-lc",
                'read -r -p "Branch name: " branch || exit; [ -n "$branch" ] || exit 1; git switch -c "$branch" "$ZED_GIT_SHA"',
            ],
            "tags": ["git-command"],
        },
        {"label": "Checkout Revision", "command": "git", "args": ["checkout", "$ZED_GIT_SHA"], "tags": ["git-command"]},
        {
            "label": "Compare with Local",
            "command": "git",
            "args": ["diff", "$ZED_GIT_SHA", "HEAD"],
            "tags": ["git-command"],
        },
        {
            "label": "Show Commit Details",
            "command": "git",
            "args": ["show", "--format=fuller", "--stat", "$ZED_GIT_SHA"],
            "tags": ["git-command"],
        },
        {
            "label": "Reset Current Branch to Here (hard)",
            "command": "git",
            "args": ["reset", "--hard", "$ZED_GIT_SHA"],
            "tags": ["git-command"],
        },
        {
            "label": "Reset Current Branch to Here (soft)",
            "command": "git",
            "args": ["reset", "--soft", "$ZED_GIT_SHA"],
            "tags": ["git-command"],
        },
        {"label": "Revert Commit", "command": "git", "args": ["revert", "$ZED_GIT_SHA"], "tags": ["git-command"]},
        {"label": "Undo Commit", "command": "git", "args": ["reset", "--soft", "HEAD~1"], "tags": ["git-command"]},
        {"label": "Fixup", "command": "git", "args": ["commit", "--fixup", "$ZED_GIT_SHA"], "tags": ["git-command"]},
        {
            "label": "Squash Into",
            "command": "bash",
            "args": [
                "-lc",
                'selected=$(git rev-parse --short "$ZED_GIT_SHA") && git rev-parse --verify "$ZED_GIT_SHA^" >/dev/null 2>&1 && export GIT_EDITOR=true GIT_SEQUENCE_EDITOR="sed -i \'/^pick $selected /s/^pick/squash/\'" && if git rev-parse --verify "$ZED_GIT_SHA^^" >/dev/null 2>&1; then git rebase -i "$ZED_GIT_SHA^^"; else git rebase -i --root; fi',
            ],
            "tags": ["git-command"],
        },
        {
            "label": "Drop Commit",
            "command": "git",
            "args": ["rebase", "--onto", "$ZED_GIT_SHA^", "$ZED_GIT_SHA"],
            "tags": ["git-command"],
        },
        {
            "label": "Interactively Rebase from Here",
            "command": "git",
            "args": ["rebase", "-i", "$ZED_GIT_SHA^"],
            "tags": ["git-command"],
        },
        {
            "label": "Push All up to Here",
            "command": "bash",
            "args": ["-lc", 'git push origin "$ZED_GIT_SHA:refs/heads/$(git branch --show-current)"'],
            "tags": ["git-command"],
        },
    ]
    for task in zed_tasks:
        task["hide"] = "on_success"

    server.shell(
        name="Install zed",
        commands=[
            f"curl -f https://raw.githubusercontent.com/zed-industries/zed/refs/tags/{zed_version}/script/install.sh | sh"
        ],
        _if=lambda: host.get_fact(File, f"/home/{user}/.local/bin/zed") is None,
    )

    installed_delta_version = (
        host.get_fact(Command, f"/home/{user}/.local/delta.app/bin/delta-app --version 2>/dev/null || true") or ""
    ).strip()

    server.shell(
        name="Install delta",
        commands=[
            f"curl -fL https://releases.delta.dev/releases/stable/{delta_version}/delta-linux-x86_64.tar.gz | tar -xz -C /tmp",
            "bash /tmp/Delta/install.sh",
        ],
        _if=lambda: installed_delta_version != f"delta {delta_version}",
    )

    if host.get_fact(Link, f"/home/{user}/bin/zed") is None:
        files.link(
            name="Create a symbolic link for zed",
            path=f"/home/{user}/bin/zed",
            target=f"/home/{user}/.local/bin/zed",
            user=user,
            group=user,
        )

    files.directory(
        name="Create zed config dir",
        path=f"/home/{user}/.config/zed",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Provision zed config",
        src=io.StringIO(json.dumps(zed_config, indent=4)),
        dest=f"/home/{user}/.config/zed/settings.json",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Provision zed keymap",
        src=io.StringIO(json.dumps(zed_keymap, indent=4)),
        dest=f"/home/{user}/.config/zed/keymap.json",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Provision zed tasks",
        src=io.StringIO(json.dumps(zed_tasks, indent=4)),
        dest=f"/home/{user}/.config/zed/tasks.json",
        user=user,
        group=user,
        mode="755",
    )

    if zed["enable_helm_support"] and host.get_fact(Directory, f"{HOMEBREW_CELLAR}/helm-ls") is None:
        server.shell(
            name="Install helm language server",
            commands=[user_brew_bin(user) + " install helm-ls"],
        )
