"""Extend char limit Note

Revision ID: 384e6782562b
Revises: 
Create Date: 2024-08-29 10:51:23.814451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String
from sqlalchemy.sql.type_api import TypeEngine

# revision identifiers, used by Alembic.
revision: str = "384e6782562b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "note_organisation",
        "value",
        type_=String(10_000),
    )


def downgrade() -> None:
    res = op.execute(
        """
        SELECT *
        FROM note_organisation
        WHERE LENGTH(value)>1800
        """
    )
    breakpoint()
    op.alter_column(
        "note_organisation",
        "value",
        type_=String(1800),
    )
