"""Corrections tied to the sentences and claims they correct.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Mark correction sections, and add the judgements and links of the corrections pass."""
    op.add_column("chunks", sa.Column("is_correction", sa.Integer, nullable=False, server_default="0"))
    # One row per correction section that was judged: the key says what it was judged against, so an unchanged
    # correction with unchanged claims is not judged again.
    op.create_table(
        "correction_judgements",
        sa.Column("correction_chunk_id", sa.Text, sa.ForeignKey("chunks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("judged_key", sa.Text, nullable=False),
        sa.Column("model", sa.Text, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False),
    )
    # One row per corrected sentence and overturned claim; claim_id is null when the sentence has no claim, or the
    # correction changes the sentence without overturning any of its claims.
    op.create_table(
        "correction_links",
        sa.Column(
            "correction_chunk_id",
            sa.Text,
            sa.ForeignKey("correction_judgements.correction_chunk_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("correction_n", sa.Integer, nullable=False),
        sa.Column("target_chunk_id", sa.Text, nullable=False),
        sa.Column("target_n", sa.Integer, nullable=False),
        sa.Column("claim_id", sa.Text),
        sa.Column("reason", sa.Text, nullable=False),
    )
    op.create_index("correction_links_by_target", "correction_links", ["target_chunk_id", "claim_id"])


def downgrade() -> None:
    """Drop the corrections pass's tables and the correction mark."""
    op.drop_table("correction_links")
    op.drop_table("correction_judgements")
    with op.batch_alter_table("chunks") as batch:
        batch.drop_column("is_correction")
