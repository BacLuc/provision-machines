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
    "openwebui_caller_key": "...",
    "openwebui_admin_key": "sk-...",
}
```

Every one of those keys is required — the `aisix validate` pre-flight in
`deploys/openwebui/deploy.py` fails the deploy while any of them is empty,
because AISIX rejects an unset or empty `${VAR}`. No real secret goes in `all.py`.

Swapping a model behind a router alias is a one-line change in the same file, for
example `openwebui = {"zen_model_quick": "novita/deepseek/deepseek-v3.2"}` — the
`router-*` names in `resources.yaml` and in `DEFAULT_MODELS` do not change.
