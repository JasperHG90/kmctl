"""kmaudit: the claims a folder of markdown docs makes about its repository, and the checks that test them.

kmaudit calls no model here. A coding agent takes sections with ``kmaudit
claims todo``, writes one verdict per sentence and stores them with
``kmaudit claims submit``; this package cuts the sections, validates the
answer and keeps it in a git-ignored SQLite store.
"""


class AuditError(Exception):
    """A refusal from a ``kmaudit`` verb; its message names what was refused and the fix."""
