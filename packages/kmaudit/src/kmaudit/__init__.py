"""kmaudit: the claims a folder of markdown docs makes about its repository, and the checks that test them.

kmaudit runs inside a coding agent's harness and uses that agent's model,
not one of its own. The agent takes sections with the
``claims_todo`` MCP tool, writes one verdict per sentence and stores them
with ``claims_submit``; this package cuts the sections, validates the
answer and keeps it in a git-ignored SQLite store.
"""


class AuditError(Exception):
    """A refusal from a ``kmaudit`` verb; its message names what was refused and the fix."""
