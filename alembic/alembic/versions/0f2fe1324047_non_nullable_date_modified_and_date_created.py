"""Make columns date_modified and date_created non-nullable in table aiod_entry

Revision ID: 0f2fe1324047
Revises: 279e17c48ea1
Create Date: 2024-10-31 16:37:23.196383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0f2fe1324047"
down_revision: Union[str, None] = "279e17c48ea1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for column in ["date_created", "date_modified"]:
        op.alter_column(
            "aiod_entry",
            column,
            existing_type=sa.DateTime(),
            nullable=False,
        )


def downgrade() -> None:
    for column in ["date_created", "date_modified"]:
        op.alter_column(
            "aiod_entry",
            column,
            existing_type=sa.DateTime(),
            nullable=True,
        )
