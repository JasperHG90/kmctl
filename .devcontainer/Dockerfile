FROM jhginn/devcontainer:ubuntu2404-pyuv312-latest-just

# The base image keeps the uv cache in the workspace so uv can hardlink from it.
# Here the cache lives in a named volume instead (see devcontainer.json), on a
# different filesystem from .venv, so uv copies rather than hardlinks.
ENV UV_CACHE_DIR=/home/vscode/.cache/uv
ENV UV_LINK_MODE=copy
ENV PREK_HOME=/home/vscode/.cache/prek
# Claude Code keeps .claude.json inside this directory instead of in $HOME, so
# one volume holds all of its state: login, settings, plugins, sessions.
ENV CLAUDE_CONFIG_DIR=/home/vscode/.claude

USER vscode
WORKDIR /home/vscode

# Create the volume mount points owned by vscode. Docker copies a directory's
# owner into a new named volume, so the volumes start out writable.
RUN mkdir -p /home/vscode/.claude /home/vscode/.cache/uv /home/vscode/.cache/prek

RUN uv tool install prek

RUN curl -fsSL --retry 5 --retry-delay 10 --retry-all-errors https://claude.ai/install.sh | bash

# Install rtk
RUN curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

# Install codegraph
RUN curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh

ENV PATH="/home/vscode/.local/bin:$PATH"
