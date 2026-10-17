#!/usr/bin/env bash
# Runs the Langfuse replay spike with keys read from ~/.bashrc, passed by environment only.
set -u
LANGFUSE_PUBLIC_KEY=$(bash -ic 'printf %s "$LANGFUSE_PUBLIC_KEY"' 2>/dev/null)
LANGFUSE_SECRET_KEY=$(bash -ic 'printf %s "$LANGFUSE_SECRET_KEY"' 2>/dev/null)
LANGFUSE_BASE_URL=$(bash -ic 'printf %s "${LANGFUSE_BASE_URL:-https://cloud.langfuse.com}"' 2>/dev/null)
export LANGFUSE_PUBLIC_KEY LANGFUSE_SECRET_KEY LANGFUSE_BASE_URL
exec uv run -q --script "$(dirname "$0")/replay.py" "$@"
