"""Optional LangSmith tracing for kmaudit's one model call, off unless ``LANGSMITH_TRACING=true``.

LangSmith reads the rest from its own variables (``LANGSMITH_API_KEY``,
``LANGSMITH_PROJECT``). langsmith is in the ``kmaudit`` extra and is
imported only when tracing is on.
"""

import os
from collections.abc import Callable


def tracing_on() -> bool:
    """Whether ``LANGSMITH_TRACING`` is set to true."""
    return os.environ.get("LANGSMITH_TRACING", "").strip().lower() == "true"


def traced[F: Callable[..., object]](fn: F, name: str) -> F:
    """``fn`` wrapped as a LangSmith ``llm`` span when tracing is on, else ``fn`` itself."""
    if not tracing_on():
        return fn
    from langsmith import traceable

    wrapped: F = traceable(run_type="llm", name=name)(fn)
    return wrapped
