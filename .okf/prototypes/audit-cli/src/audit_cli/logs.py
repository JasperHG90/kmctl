"""Structured logging: every run appends JSON lines to the project's log file, and nothing goes to the terminal."""

import logging
import pathlib as plb
from typing import TextIO

import structlog

_handle: TextIO | None = None


def configure_logging(path: plb.Path, level: str) -> None:
    """Send structlog's events to ``path`` as JSON lines, keeping events at ``level`` and above.

    Calling it again (as tests do) closes the previous file first.
    """
    global _handle  # one log file per process
    if _handle is not None:
        _handle.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    _handle = path.open("a", encoding="utf-8")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelNamesMapping()[level.upper()]),
        logger_factory=structlog.WriteLoggerFactory(file=_handle),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str) -> structlog.typing.FilteringBoundLogger:
    """Return a logger whose events carry ``name`` as their component."""
    logger: structlog.typing.FilteringBoundLogger = structlog.get_logger(component=name)
    return logger
