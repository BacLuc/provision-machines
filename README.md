# PyInfra project to provision development machines

## Setup uv

```shell
# renovate: datasource=github-releases depName=astral-sh/uv
UV_VERSION=0.11.25
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

# Run with opencode-desktop

cat ~/.local/share/applications/ai.opencode.desktop.desktop
[Desktop Entry]
Name=OpenCode
Exec=env OPENCODE_CONFIG=/home/${USER}/.opencode/untracked-config.json /opt/OpenCode/ai.opencode.desktop --auto %U
Terminal=false
Type=Application
Icon=ai.opencode.desktop
StartupWMClass=ai.opencode.desktop
MimeType=x-scheme-handler/opencode;
Categories=Development;%
