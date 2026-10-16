test:
    uv run pytest

# The tests that reach GitHub, left out of `just test` (the integration gate).
integration:
    uv run pytest -m integration

lint:
    uv run ruff check
    uv run ruff format --check
