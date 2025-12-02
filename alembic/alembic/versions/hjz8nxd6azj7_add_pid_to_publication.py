"""Add pid to publication

Revision ID: hjz8nxd6azj7
Revises: 79b2dda7e3be
Create Date: 2025-12-03 03:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String

from database.model.field_length import NORMAL

# revision identifiers, used by Alembic.
revision: str = "hjz8nxd6azj7"
down_revision: Union[str, None] = "79b2dda7e3be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        table_name="publication",
        column=Column("pid", String(NORMAL), nullable=True),
    )


def downgrade() -> None:
    op.drop_column(table_name="publication", column_name="pid")
