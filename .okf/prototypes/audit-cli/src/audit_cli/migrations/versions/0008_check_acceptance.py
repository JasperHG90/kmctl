"""Check acceptance: a weak check a person (or a failed rewrite) accepted as the best there is, and the last rewrite.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add acceptance and the key of the last attempt to strengthen a weak check to its quality row."""
    with op.batch_alter_table("check_quality") as batch:
        batch.add_column(sa.Column("accepted_by", sa.Text, nullable=False, server_default=""))
        batch.add_column(sa.Column("accepted_note", sa.Text, nullable=False, server_default=""))
        batch.add_column(sa.Column("strengthen_key", sa.Text, nullable=False, server_default=""))


def downgrade() -> None:
    """Drop the acceptance columns."""
    with op.batch_alter_table("check_quality") as batch:
        batch.drop_column("strengthen_key")
        batch.drop_column("accepted_note")
        batch.drop_column("accepted_by")
