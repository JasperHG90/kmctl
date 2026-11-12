#!/bin/bash

set -e

echo "Configuring development container..."

workspace="${1:-/home/vscode/workspace}"

# Docker creates a named volume owned by root when the image has nothing at the
# mount point, which is the case for .venv under the bind-mounted workspace and
# for the worktrees folder.
sudo chown -R vscode:vscode \
  /home/vscode/.claude \
  /home/vscode/.cache/uv \
  /home/vscode/.cache/prek \
  "${workspace}/.venv" \
  "${workspace}.worktrees"

# Ticket records made on the Mac hold worktree paths under the host checkout.
# Point those paths at the workspace and its worktrees so loopctl resolves them.
sudo mkdir -p /Users/jasperginn/Documents/code_projects
sudo ln -sfn "${workspace}" /Users/jasperginn/Documents/code_projects/kmctl
sudo ln -sfn "${workspace}.worktrees" /Users/jasperginn/Documents/code_projects/kmctl.worktrees

cd "${workspace}"

uv sync

# The pre-commit hooks in .pre-commit-config.yaml, behind loopctl's git hook.
just hooks
