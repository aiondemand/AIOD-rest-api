"""Add news.source

Revision ID: d09ed8ad4533
Revises: 0f2fe1324047
Create Date: 2024-11-21 09:36:49.556254

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import Column, String

from database.model.field_length import LONG

# revision identifiers, used by Alembic.
revision: str = "d09ed8ad4533"
down_revision: Union[str, None] = "0f2fe1324047"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        table_name="news",
        column=Column("source", String(LONG), nullable=True),
    )


def downgrade() -> None:
    op.drop_column(table_name="news", column_name="source")
