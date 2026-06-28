# renovate: datasource=docker depName=mcr.microsoft.com/devcontainers/universal
FROM mcr.microsoft.com/devcontainers/universal:6.0.6-noble@sha256:c496c89fedfb24148aac7918c0d6ee217e7deed476dad6e6e8c867b9439e3f37

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

ENV NVM_DIR=/home/codespace/.nvm
# renovate: datasource=github-releases depName=nvm-sh/nvm
ENV NVM_VERSION=0.40.5
# renovate: datasource=github-tags depName=nodejs/node
ENV NODE_VERSION=26.4.0
# renovate: datasource=npm depName=@google/gemini-cli
ENV GEMINI_CLI_VERSION=0.49.0
# renovate: datasource=npm depName=@openai/codex
ENV CODEX_VERSION=0.142.4

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh | bash && \
    . /home/codespace/.nvm/nvm.sh && \
    nvm install ${NODE_VERSION} && \
    curl -fsSL https://claude.ai/install.sh | bash && \
    npm install -g opencode-ai @google/gemini-cli@${GEMINI_CLI_VERSION} @openai/codex@${CODEX_VERSION} && \
    curl -fsSL https://antigravity.google/cli/install.sh | bash

ENV OPENCODE_CONFIG=/home/codespace/.config/opencode/untracked-config.json

ENV OPENCODE_PORT=4096

USER root

# Add nvm initialization for interactive zsh sessions.
# /etc/zsh/zshrc is sourced for every interactive zsh shell and is NOT part of
# the home volume, so this works for new and existing home volumes alike.
RUN printf '\n# NVM initialization\nexport NVM_DIR="/home/codespace/.nvm"\n[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"\n' >> /etc/zsh/zshrc

COPY init-home.sh /usr/local/bin/init-ai-devcontainer-home
RUN chmod +x /usr/local/bin/init-ai-devcontainer-home
