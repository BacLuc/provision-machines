# renovate: datasource=docker depName=mcr.microsoft.com/devcontainers/base
FROM mcr.microsoft.com/devcontainers/base:2-noble@sha256:3dcb059253b2ebb44de3936620e1cff3dadcd2c1c982d579081ca8128c1eb319

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
