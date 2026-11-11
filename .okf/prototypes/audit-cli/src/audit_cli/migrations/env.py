"""Alembic's environment: run the migrations on the connection the store hands over."""

from alembic import context

connection = context.config.attributes["connection"]
# Batch mode lets SQLite alter tables by copying them, which plain ALTER TABLE cannot always do.
context.configure(connection=connection, target_metadata=None, render_as_batch=True)
with context.begin_transaction():
    context.run_migrations()
