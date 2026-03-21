# renovate: datasource=docker depName=mcr.microsoft.com/devcontainers/universal
FROM mcr.microsoft.com/devcontainers/universal:5.1.5-noble@sha256:5035562d736642e6d0382d4ef599d84d43f428609ae17fbe2e841b30451de0f7

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
