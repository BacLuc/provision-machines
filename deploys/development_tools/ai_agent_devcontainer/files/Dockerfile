# renovate: datasource=docker depName=mcr.microsoft.com/devcontainers/universal
FROM mcr.microsoft.com/devcontainers/universal:6.0.3-noble@sha256:beb3274e5487f10de92c5e02923abe13bd2f2a647e712b32c303a9e91ab7c273

RUN sudo install -d -m 0755 /etc/apt/keyrings \
    && sudo curl -fsSL https://downloads.claude.ai/keys/claude-code.asc \
      -o /etc/apt/keyrings/claude-code.asc \
    && echo "deb [signed-by=/etc/apt/keyrings/claude-code.asc] https://downloads.claude.ai/claude-code/apt/stable stable main" \
      | sudo tee /etc/apt/sources.list.d/claude-code.list \
    && apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    ansible \
    python3-pip \
    python3-apt \
    claude-code \
    curl \
    git \
    netcat-openbsd \
    && curl https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/refs/tags/v1.5.9063/files/docker/systemctl3.py -o /usr/local/bin/systemctl \
    && chmod +x /usr/local/bin/systemctl

USER codespace

ENV NVM_DIR=/home/codespace/.nvm
# renovate: datasource=github-releases depName=nvm-sh/nvm
ENV NVM_VERSION=0.40.5
# renovate: datasource=github-tags depName=nodejs/node
ENV NODE_VERSION=24
# renovate: datasource=npm depName=@google/gemini-cli
ENV GEMINI_CLI_VERSION=0.45.2
# renovate: datasource=npm depName=@openai/codex
ENV CODEX_VERSION=0.137.0

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh | bash && \
    . /home/codespace/.nvm/nvm.sh && \
    nvm install ${NODE_VERSION} && \
    npm install -g opencode-ai @google/gemini-cli@${GEMINI_CLI_VERSION} @openai/codex@${CODEX_VERSION} && \
    curl -fsSL https://antigravity.google/cli/install.sh | bash

ENV OPENCODE_CONFIG=/home/codespace/.config/opencode/untracked-config.json

ENV OPENCODE_PORT=4096

USER root
