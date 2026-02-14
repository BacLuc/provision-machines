# renovate: datasource=docker depName=mcr.microsoft.com/devcontainers/base
FROM mcr.microsoft.com/devcontainers/base:1-noble@sha256:763eca1839b2c6366f25b9c2b4c75c46e3d485a8d1b95f725e829397398a4c46

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    ansible \
    python3-pip \
    python3-apt \
    curl \
    git \
    && curl https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/refs/tags/v1.5.9063/files/docker/systemctl3.py -o /usr/local/bin/systemctl \
    && chmod +x /usr/local/bin/systemctl

USER vscode

ENV NVM_DIR=/home/vscode/.nvm
# renovate: datasource=github-releases depName=nvm-sh/nvm
ENV NVM_VERSION=0.40.0
# renovate: datasource=github-tags depName=nodejs/node
ENV NODE_VERSION=24

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh | bash && \
    . /home/vscode/.nvm/nvm.sh && \
    nvm install ${NODE_VERSION} && \
    npm install -g opencode-ai

USER root
