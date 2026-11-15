"""Checks: each claim's steps or reason, the files they read, their last result, triage, a cache and each pass.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the checks stage's tables."""
    # One row per claim: a check (steps), a reason no step can test it, or a verdict settled with no model. Keyed by
    # claim_id, which follows the claim's text, so a changed claim is a new row and its old row is pruned.
    op.create_table(
        "checks",
        sa.Column("claim_id", sa.Text, primary_key=True),
        sa.Column("kind", sa.Text, nullable=False),  # check, reason or settled
        sa.Column("steps", sa.Text),  # JSON list of steps, for a check
        sa.Column("strength", sa.Text),  # exact or proxy, for a check
        sa.Column("why", sa.Text, nullable=False, server_default=""),
        sa.Column("settled", sa.Integer),  # 1 or 0, for a claim settled with no model
        sa.Column("writer", sa.Text, nullable=False),  # what wrote it: settle, twocall:<model>, agent:<model>
        sa.Column("prompt_hash", sa.Text, nullable=False, server_default=""),
        sa.Column("expectation_changed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens", sa.Integer, nullable=False, server_default="0"),  # its share of the calls that wrote it
        sa.Column("commit_sha", sa.Text, nullable=False, server_default=""),
        sa.Column("written_at", sa.Text, nullable=False),
    )
    # The files a check read when it last ran (for a reason: the files its lines came from), with each file's content
    # hash, and the globs its steps name; a change to either sends the check back.
    op.create_table(
        "check_reads",
        sa.Column("claim_id", sa.Text, sa.ForeignKey("checks.claim_id", ondelete="CASCADE"), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("sha", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("claim_id", "path"),
    )
    # The last run of each check: whether it held, what each step saw, and the reads it ran against.
    op.create_table(
        "check_results",
        sa.Column("claim_id", sa.Text, sa.ForeignKey("checks.claim_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("holds", sa.Integer, nullable=False),
        sa.Column("results", sa.Text, nullable=False),
        sa.Column("reads_key", sa.Text, nullable=False),
        sa.Column("commit_sha", sa.Text, nullable=False, server_default=""),
        sa.Column("ran_at", sa.Text, nullable=False),
    )
    # A decision model's answer about a claim: why its check failed (failure), or what its lines show (judge). The key
    # says what was asked, so the same question is not asked twice.
    op.create_table(
        "check_triage",
        sa.Column("claim_id", sa.Text, sa.ForeignKey("checks.claim_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("asked_key", sa.Text, nullable=False),
        sa.Column("model", sa.Text, nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("verdict", sa.Text, nullable=False),
        sa.Column("answers", sa.Text, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False),
    )
    # Slow facts about the repository (its CLI commands and their flags), kept under a key of what they depend on.
    op.create_table(
        "cache",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False),
    )
    # One row per checks command run: what it did and spent, to measure the stage over time.
    op.create_table(
        "check_passes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("verb", sa.Text, nullable=False),
        sa.Column("started_at", sa.Text, nullable=False),
        sa.Column("seconds", sa.Float, nullable=False),
        sa.Column("report", sa.Text, nullable=False),
    )


def downgrade() -> None:
    """Drop the checks stage's tables."""
    for table in ("check_passes", "cache", "check_triage", "check_results", "check_reads", "checks"):
        op.drop_table(table)
