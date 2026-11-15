"""The project, files, chunks and the claims stage.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the first tables."""
    op.create_table(
        "project",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("root", sa.Text, nullable=False),
        sa.Column("seen_at", sa.Text, nullable=False),
    )
    op.create_table(
        "files",
        sa.Column("path", sa.Text, primary_key=True),
        sa.Column("sha256", sa.Text, nullable=False),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("lang", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("is_text", sa.Integer, nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("read_at", sa.Text, nullable=False),
    )
    op.create_table(
        "chunks",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("position", sa.Integer, nullable=False, comment="The section's order within its concept."),
        sa.Column("concept", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("status", sa.Text),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("section", sa.Text, nullable=False),
        sa.Column("sentences", sa.Text, nullable=False, comment="JSON list."),
        sa.Column("corrections", sa.Text, nullable=False),
        sa.Column("key", sa.Text, nullable=False),
        sa.Column("extraction_key", sa.Text, nullable=False),
        sa.Column("earlier", sa.Text, nullable=False),
        sa.Column("earlier_ids", sa.Text, nullable=False, comment="JSON list."),
        sa.Column("chunked_at", sa.Text, nullable=False),
    )
    # The claims stage's cache: one row per chunk content and run. A changed chunk, model, prompt or salt is a new
    # row. Only answers the model gave in a readable form are stored; an unreadable one is asked again next pass.
    op.create_table(
        "claim_extractions",
        sa.Column("extraction_key", sa.Text, nullable=False),
        sa.Column("model", sa.Text, nullable=False),
        sa.Column("prompt_hash", sa.Text, nullable=False),
        sa.Column("salt", sa.Text, nullable=False),
        sa.Column("chunk_id", sa.Text, nullable=False),
        sa.Column("claims", sa.Text, nullable=False, comment="JSON list of claims."),
        sa.Column("error", sa.Text),
        sa.Column("tokens_in", sa.Integer, nullable=False),
        sa.Column("tokens_out", sa.Integer, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("extraction_key", "model", "prompt_hash", "salt"),
    )
    # The merged claims of each chunk's latest extraction.
    op.create_table(
        "claims",
        sa.Column("chunk_id", sa.Text, sa.ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("claim_id", sa.Text, nullable=False),
        sa.Column("concept", sa.Text, nullable=False),
        sa.Column("sentence_n", sa.Integer, nullable=False),
        sa.Column("sentence", sa.Text, nullable=False),
        sa.Column("claim_type", sa.Text, nullable=False),
        sa.Column("claim", sa.Text, nullable=False),
        sa.Column("how_to_check", sa.Text, nullable=False),
        sa.Column("quantifier", sa.Text, nullable=False),
        sa.Column("refers_to", sa.Text, nullable=False, comment="JSON list of 'chunk id|n'."),
        sa.Column("run", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("chunk_id", "position"),
    )
    op.create_index("claims_by_claim_id", "claims", ["claim_id"])
    op.create_index("claims_by_type", "claims", ["claim_type"])


def downgrade() -> None:
    """Drop the first tables."""
    for table in ["claims", "claim_extractions", "chunks", "files", "project"]:
        op.drop_table(table)
