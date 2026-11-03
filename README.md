# PyInfra project to provision development machines

## Setup uv

```shell
# renovate: datasource=github-releases depName=astral-sh/uv
UV_VERSION=0.12.18
curl -Ls https://releases.astral.sh/github/uv/releases/download/$UV_VERSION/uv-x86_64-unknown-linux-gnu.tar.gz | tar -xzC ~/.local/bin --strip-components=1
chmod +x ~/.local/bin/uv
```

Install the dependencies:

```shell
uv sync --all-extras
```

## Run pyinfra

```shell
uv run scripts/run_pyinfra_local.py
```

## Lint

```shell
uv run scripts/lint.py
```

## Machine-specific secrets

`group_data/local.py` is gitignored and deep-merged over `group_data/all.py` last.
Put machine-specific secrets there, e.g. the `openwebui` keys:

```python
openwebui = {
    "opencode_api_key": "sk-...",
    "opencode_api_key_2": "sk-...",
    "opencode_api_key_3": "sk-...",
    "requesty_api_key": "sk-...",
    "cortecs_api_key": "sk-...",
    "openwebui_caller_key": "sk-...",
}
```

Those six keys are written from `local.py` into the mode-600 `.env`, which both
`env_file` services read. Every `${VAR}` that
`deploys/openwebui/files/resources.yaml` interpolates — 14 of them — must be set to a
non-empty value: the `Validate aisix resources before starting the stack` pre-flight
in `deploys/openwebui/deploy.py` runs `aisix validate` before the systemd unit starts
the stack, and it exits 1 naming the variable, e.g.
``key_env environment variable `OPENWEBUI_CALLER_KEY` is unset or empty``.
No real secret goes in `all.py`.

The full variable set is in `deploys/openwebui/files/env.example`; a new variable
needs a group-data key and an `env.example` line, not a compose edit. The one
compose-only literal is `WEBUI_AUTH=False` — a pin in `environment:`, which
deliberately wins over `.env`.

## Firefox taskbar tabs

The created taskbar tab PWAs come from `group_data/local.py`; the defaults live in
`deploys/firefox_taskbar_tabs/deploy.py`. Icons for every supported app are committed
in `deploys/firefox_taskbar_tabs/files/icons/<key>-256.png`.

```python
firefox_taskbar_tabs = {
    "enabled": True,
    "tabs": {
        "vshn-gitlab": {
            "name": "VSHN GitLab",
            "url": "https://git.vshn.net/",
            "tab_id": "44f1788e-8889-4097-8d8d-da60a1c68a06",
            "keywords": ["gitlab"],
        },
    },
}
```

`tab_id` is a stable UUID per app (`python3 -c "import uuid; print(uuid.uuid4())"`). The app
grid search always matches the `name` and the tab key; extra `keywords` add more terms.
Removing an entry from `local.py` or setting `"enabled": False` on it removes its taskbar tab
from the Firefox registries and its app grid entry on the next deploy run; re-enabling or
re-adding restores it (the profile directories stay around).

`url_prefixes` optionally lists https URL prefixes that open in the taskbar tab instead of
the browser: a wrapper script (default handler for `x-scheme-handler/https`) routes matching
URLs, e.g. `"url_prefixes": ["https://vshn.zoom.us/j/"]` sends meeting links into the Zoom
window. Unmatched URLs open in the browser as usual. Removing all `url_prefixes` deletes the
wrapper and its handler .desktop file but leaves the scheme registration; reset it manually
with `xdg-mime default firefox_firefox.desktop x-scheme-handler/https`.
