import json
from pyinfra import host
from pyinfra.operations import files, server

user = host.data.get("user", "ubuntu")

zed_defaults = {
    "enable_helm_support": True,
    "enable_memory_monitor": True,
    "memory_monitor_limit_gb": 10,
    "memory_monitor_cron_frequency": "*/5 * * * *",
    "zed_config": {
        "language_models": {
            "openai_compatible": {
                "cortecs": {
                    "api_url": "https://api.cortecs.ai/v1/",
                    "available_models": [
                        {
                            "name": "devstral-2512",
                            "max_tokens": 200000,
                            "max_output_tokens": 32000,
                            "max_completion_tokens": 200000,
                            "capabilities": {
                                "tools": True,
                                "images": False,
                                "parallel_tool_calls": False,
                                "prompt_cache_key": False,
                                "chat_completions": True,
                            },
                        },
                        {
                            "name": "gpt-oss-120b",
                            "max_tokens": 200000,
                            "max_output_tokens": 32000,
                            "max_completion_tokens": 200000,
                            "capabilities": {
                                "tools": True,
                                "images": False,
                                "parallel_tool_calls": False,
                                "prompt_cache_key": False,
                                "chat_completions": True,
                            },
                        },
                        {
                            "name": "claude-opus4-5",
                            "max_tokens": 200000,
                            "max_output_tokens": 32000,
                            "max_completion_tokens": 200000,
                            "capabilities": {
                                "tools": True,
                                "images": False,
                                "parallel_tool_calls": True,
                                "prompt_cache_key": False,
                                "chat_completions": True,
                            },
                        },
                        {
                            "name": "qwen3-next-80b-a3b-thinking",
                            "max_tokens": 200000,
                            "max_output_tokens": 32000,
                            "max_completion_tokens": 200000,
                            "capabilities": {
                                "tools": True,
                                "images": False,
                                "parallel_tool_calls": False,
                                "prompt_cache_key": False,
                                "chat_completions": True,
                            },
                        },
                        {
                            "name": "kimi-k2-thinking",
                            "max_tokens": 200000,
                            "max_output_tokens": 32000,
                            "max_completion_tokens": 200000,
                            "capabilities": {
                                "tools": True,
                                "images": False,
                                "parallel_tool_calls": False,
                                "prompt_cache_key": False,
                                "chat_completions": True,
                            },
                        },
                        {
                            "name": "qwen3-coder-30b-a3b-instruct",
                            "max_tokens": 200000,
                            "max_output_tokens": 32000,
                            "max_completion_tokens": 200000,
                            "capabilities": {
                                "tools": True,
                                "images": False,
                                "parallel_tool_calls": False,
                                "prompt_cache_key": False,
                                "chat_completions": True,
                            },
                        },
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
            "copilot": {
                "proxy": None,
                "proxy_no_verify": None,
                "enterprise_uri": None,
            },
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
    },
    "zed_keymap": [{"context": "Editor", "bindings": {"ctrl-k": None}}],
}

zed = zed_defaults.copy()
if host.data.get("zed"):
    zed.update(host.data.get("zed", {}))

if host.data.get("enable_zed", False):
    
    server.shell(
        name="Install zed",
        commands=["curl -f https://raw.githubusercontent.com/zed-industries/zed/refs/tags/v0.204.5/script/install.sh | sh"],
    )
    
    files.file(
        name="Check if zed symlink needs creation",
        path=f"/home/{user}/bin/zed",
    )
    
    files.link(
        name="Create a symbolic link for zed",
        src=f"/home/{user}/.local/bin/zed",
        dest=f"/home/{user}/bin/zed",
    )
    
    files.directory(
        name="Create zed config dir",
        path=f"/home/{user}/.config/zed",
        mode="755",
    )
    
    files.put(
        name="Provision zed config",
        dest=f"/home/{user}/.config/zed/settings.json",
        content=json.dumps(zed["zed_config"], indent=2),
        mode="755",
    )
    
    files.put(
        name="Provision zed keymap",
        dest=f"/home/{user}/.config/zed/keymap.json",
        content=json.dumps(zed["zed_keymap"], indent=2),
        mode="755",
    )
    
    files.put(
        name="Add launch zed script",
        dest=f"/home/{user}/bin/launch-zed-with-env",
        content=f"""#!/usr/bin/env zsh

ZED_ENVIRONMENT=cli
ZED_FORCE_CLI_MODE=
ZED_TERM=true

source /home/{user}/.zshrc
exec zed "$@"
""",
        mode="755",
    )
    
    files.put(
        name="Change zed desktop file to use environment",
        dest=f"/home/{user}/.local/share/applications/dev.zed.Zed.desktop",
        content=f"""[Desktop Entry]
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
""",
        mode="644",
    )
    
    if zed.get("enable_memory_monitor", False):
        # Memory monitor implementation would go here
        pass
    
    if zed.get("enable_helm_support", False):
        server.shell(
            name="Install helm language server",
            commands=[f"{host.data.get('homebrew_binaries_path', f'/home/{user}/bin')}/brew install helm-ls"],
        )