"""Check quality: how many mutants of its code a holding check noticed, and whether it tests what its claim says.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add one row per check: its mutation score (no model) and its link score (decision model), each with the key
    of what it was measured on, so neither is measured twice for the same check and code."""
    op.create_table(
        "check_quality",
        sa.Column("claim_id", sa.Text, sa.ForeignKey("checks.claim_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("mutants", sa.Integer),
        sa.Column("killed", sa.Integer),
        sa.Column("survived", sa.Text, nullable=False, server_default="[]"),
        sa.Column("mutant_key", sa.Text, nullable=False, server_default=""),
        sa.Column("link_score", sa.Float),
        sa.Column("link_verdict", sa.Text),
        sa.Column("link_key", sa.Text, nullable=False, server_default=""),
    )


def downgrade() -> None:
    """Drop the check quality table."""
    op.drop_table("check_quality")
