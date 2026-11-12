"""Claims an OKF bundle makes about its repository: sections to read, the answer schema and the store.

kmctl calls no model here. A coding agent takes sections with ``kmctl audit
claims todo``, writes one verdict per sentence and stores them with ``kmctl
audit claims submit``; this package cuts the sections, validates the answer
and keeps it in a git-ignored SQLite store.
"""


class AuditError(Exception):
    """A refusal from a ``kmctl audit`` verb; its message names what was refused and the fix."""
