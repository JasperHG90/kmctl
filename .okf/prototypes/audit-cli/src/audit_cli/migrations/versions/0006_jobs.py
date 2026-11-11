"""Jobs: each audit checks run, in the foreground or in the background, with its stage and progress.

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add one row per run: what it is doing, how far it got, what it spent, and how it ended."""
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("verb", sa.Text, nullable=False),
        sa.Column("args", sa.Text, nullable=False, server_default="[]"),
        sa.Column("pid", sa.Integer),
        sa.Column("status", sa.Text, nullable=False),  # starting, running, done, failed, stopped, died
        sa.Column("stage", sa.Text, nullable=False, server_default=""),
        sa.Column("done", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.Text, nullable=False),
        sa.Column("updated_at", sa.Text, nullable=False),
        sa.Column("finished_at", sa.Text),
        sa.Column("log_path", sa.Text, nullable=False, server_default=""),
        sa.Column("summary", sa.Text, nullable=False, server_default="{}"),
        sa.Column("error", sa.Text, nullable=False, server_default=""),
    )


def downgrade() -> None:
    """Drop the jobs table."""
    op.drop_table("jobs")
