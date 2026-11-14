"""Fixtures for the repository-level tests.

kmctl's own tests keep their fixtures in packages/kmctl/tests/conftest.py;
these tests share only the per-run uv cache with them.
"""

import os
import shutil
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True, scope="session")
def _uv_cache(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Give the run its own uv cache, and delete it when the run ends.

    The wheel build, smoke and release tests start uv, which keeps every
    environment it builds in its cache for good. Without this, running these
    tests alone (`uv run pytest tests -m integration`) grows the shared cache.
    """
    cache = tmp_path_factory.mktemp("uv-cache")
    saved = os.environ.get("UV_CACHE_DIR")
    os.environ["UV_CACHE_DIR"] = str(cache)
    yield
    if saved is None:
        os.environ.pop("UV_CACHE_DIR", None)
    else:
        os.environ["UV_CACHE_DIR"] = saved
    shutil.rmtree(cache, ignore_errors=True)
