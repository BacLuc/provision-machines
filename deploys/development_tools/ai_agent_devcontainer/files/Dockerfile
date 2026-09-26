# renovate: datasource=docker depName=mcr.microsoft.com/devcontainers/universal
FROM mcr.microsoft.com/devcontainers/universal:6.1.7-noble@sha256:584e41561451c910dcd96221634be07545803aed9cd437a60288f06ddeaf5880

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    ansible \
    python3-pip \
    python3-apt \
    curl \
    git \
    netcat-openbsd \
    && curl https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/refs/tags/v1.5.9063/files/docker/systemctl3.py -o /usr/local/bin/systemctl \
    && chmod +x /usr/local/bin/systemctl

USER codespace

ENV NVM_DIR=/usr/local/share/nvm
# renovate: datasource=github-tags depName=nodejs/node
ENV NODE_VERSION=26.7.0
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ENV CLAUDE_CODE_VERSION=2.1.281
# renovate: datasource=npm depName=@google/gemini-cli
ENV GEMINI_CLI_VERSION=0.56.0
# renovate: datasource=npm depName=@openai/codex
ENV CODEX_VERSION=0.156.1
# renovate: datasource=npm depName=opencode-ai
ENV OPENCODE_VERSION=1.18.32
# renovate: datasource=npm depName=t3
ENV T3_CODE_VERSION=0.0.42

RUN . $NVM_DIR/nvm.sh && \
    nvm install ${NODE_VERSION} && \
    nvm alias default ${NODE_VERSION} && \
    npm install -g \
      opencode-ai@${OPENCODE_VERSION} \
      @anthropic-ai/claude-code --allow-scripts=@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} \
      @google/gemini-cli@${GEMINI_CLI_VERSION} \
      @openai/codex@${CODEX_VERSION} \
      t3@${T3_CODE_VERSION} \
    && \
    curl -fsSL https://antigravity.google/cli/install.sh | bash

ENV OPENCODE_CONFIG=/home/codespace/.config/opencode/untracked-config.jsonc

ENV OPENCODE_PORT=4096

USER root

COPY init-home.sh /usr/local/bin/init-ai-devcontainer-home
RUN chmod +x /usr/local/bin/init-ai-devcontainer-home
