# renovate: datasource=docker depName=mcr.microsoft.com/devcontainers/universal
FROM mcr.microsoft.com/devcontainers/universal:6.0.3-noble@sha256:beb3274e5487f10de92c5e02923abe13bd2f2a647e712b32c303a9e91ab7c273

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    ansible \
    python3-pip \
    python3-apt \
    curl \
    git \
    && curl https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/refs/tags/v1.5.9063/files/docker/systemctl3.py -o /usr/local/bin/systemctl \
    && chmod +x /usr/local/bin/systemctl

USER codespace

ENV NVM_DIR=/home/codespace/.nvm
# renovate: datasource=github-releases depName=nvm-sh/nvm
ENV NVM_VERSION=0.40.4
# renovate: datasource=github-tags depName=nodejs/node
ENV NODE_VERSION=24

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh | bash && \
    . /home/codespace/.nvm/nvm.sh && \
    nvm install ${NODE_VERSION} && \
    npm install -g opencode-ai

ENV OPENCODE_CONFIG=/home/codespace/.config/opencode/untracked-config.json

USER root
