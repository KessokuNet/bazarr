"""Merge heads from 4274a5dfc4ad and 2a86a941ecac

Revision ID: f3e8d7c6b5a4
Revises: 4274a5dfc4ad, 2a86a941ecac
Create Date: 2025-12-18 12:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f3e8d7c6b5a4"
down_revision = ("4274a5dfc4ad", "2a86a941ecac")
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no operations needed
    pass


def downgrade():
    # This is a merge migration - no operations needed
    pass
