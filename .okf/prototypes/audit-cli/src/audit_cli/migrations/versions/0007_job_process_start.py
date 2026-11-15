"""Jobs record when their process started, so a process id reused by another program is not taken for the run.

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the process start time to each job."""
    op.add_column("jobs", sa.Column("pid_started", sa.Text, nullable=False, server_default=""))


def downgrade() -> None:
    """Drop the process start time."""
    with op.batch_alter_table("jobs") as batch:
        batch.drop_column("pid_started")
