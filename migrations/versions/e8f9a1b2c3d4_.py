"""Add overview column to table_episodes

Revision ID: e8f9a1b2c3d4
Revises: dc09994b7e65
Create Date: 2025-12-18 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e8f9a1b2c3d4"
down_revision = "dc09994b7e65"
branch_labels = None
depends_on = None

bind = op.get_context().bind
insp = sa.inspect(bind)


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    # Add overview column to table_episodes if it doesn't exist
    if not column_exists("table_episodes", "overview"):
        with op.batch_alter_table("table_episodes") as batch_op:
            batch_op.add_column(sa.Column("overview", sa.Text(), nullable=True))


def downgrade():
    # Remove overview column from table_episodes if it exists
    if column_exists("table_episodes", "overview"):
        with op.batch_alter_table("table_episodes") as batch_op:
            batch_op.drop_column("overview")
