test:
    uv run pytest

# The tests that reach GitHub, left out of `just test` (the integration gate).
integration:
    uv run pytest -m integration

lint:
    uv run ruff check
    uv run ruff format --check

# Install the pre-commit hooks in .pre-commit-config.yaml behind loopctl's git
# hook, which runs .git/hooks/pre-commit.local after its own gate.
hooks:
    printf '#!/bin/sh\nexec uvx prek@0.5.5 run\n' > .git/hooks/pre-commit.local
    chmod +x .git/hooks/pre-commit.local
