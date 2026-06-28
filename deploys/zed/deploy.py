import io
import json

from pyinfra.facts.files import Directory, File, Link

from operations.homebrew import HOMEBREW_CELLAR, user_brew_bin
from operations.user import get_user_name
from pyinfra import host
from pyinfra.operations import crontab, files, flatpak, server, systemd

user = get_user_name()
zed = host.data.zed

flatpak.packages(
    name="Remove zed flatpak",
    packages=["dev.zed.Zed"],
    present=False,
)

if zed["enabled"]:
    zed_version = "v0.204.5"

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

    server.shell(
        name="Install zed",
        commands=[
            f"curl -f https://raw.githubusercontent.com/zed-industries/zed/refs/tags/{zed_version}/script/install.sh | sh"
        ],
        _if=lambda: host.get_fact(File, f"/home/{user}/.local/bin/zed") is None,
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
        name="Add launch zed script",
        src=io.StringIO(
            f"""#!/usr/bin/env zsh

ZED_ENVIRONMENT=cli
ZED_FORCE_CLI_MODE=
ZED_TERM=true

source /home/{user}/.zshrc
exec zed "$@"
"""
        ),
        dest=f"/home/{user}/bin/launch-zed-with-env",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Change zed desktop file to use environment",
        src=io.StringIO(
            f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Zed
GenericName=Text Editor
Comment=A high-performance, multiplayer code editor.
StartupNotify=true
Terminal=true
Exec=/home/{user}/bin/launch-zed-with-env %U
Icon=/home/{user}/.local/zed.app/share/icons/hicolor/512x512/apps/zed.png
Categories=Utility;TextEditor;Development;IDE;
Keywords=zed;
MimeType=text/plain;application/x-zerosize;x-scheme-handler/zed;
Actions=NewWorkspace;
X-Desktop-File-Install-Version=0.28

[Desktop Action NewWorkspace]
Exec=/home/{user}/bin/launch-zed-with-env --new %U
Name=Open a new workspace
"""
        ),
        dest=f"/home/{user}/.local/share/applications/dev.zed.Zed.desktop",
        user=user,
        group=user,
        mode="644",
    )

    files.file(
        name="Remove the Zed memory monitoring script",
        path="/usr/local/bin/monitor-zed-memory",
        present=False,
        _sudo=True,
    )

    crontab.crontab(
        name="Remove the cron job for Zed memory monitoring",
        command="/usr/local/bin/monitor-zed-memory",
        present=False,
        user=user,
        _sudo=True,
    )

    zed_resource_limits = files.directory(
        name="Remove drop in dir for flatpak-system-helper",
        path="/etc/systemd/system/flatpak-system-helper.service.d",
        present=False,
        _sudo=True,
    )

    systemd.daemon_reload(
        name="Reload daemons",
        _sudo=True,
        _if=lambda: zed_resource_limits.changed,
    )

    if zed["enable_helm_support"] and host.get_fact(Directory, f"{HOMEBREW_CELLAR}/helm-ls") is None:
        server.shell(
            name="Install helm language server",
            commands=[user_brew_bin(user) + " install helm-ls"],
        )
