"""The model's reason for each verdict, kept for sentences with no claim too.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the reason columns and the sentence verdicts table."""
    op.add_column("claims", sa.Column("reason", sa.Text, nullable=False, server_default=""))
    op.add_column(
        "claim_extractions",
        sa.Column("verdicts", sa.Text, nullable=False, server_default="[]", comment="JSON list of sentence verdicts."),
    )
    # One row per sentence of each extracted chunk: its kind and reason, from the run whose claims it keeps.
    op.create_table(
        "sentence_verdicts",
        sa.Column("chunk_id", sa.Text, sa.ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sentence_n", sa.Integer, nullable=False),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("run", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("chunk_id", "sentence_n"),
    )


def downgrade() -> None:
    """Drop the sentence verdicts table and the reason columns."""
    op.drop_table("sentence_verdicts")
    with op.batch_alter_table("claim_extractions") as batch:
        batch.drop_column("verdicts")
    with op.batch_alter_table("claims") as batch:
        batch.drop_column("reason")
