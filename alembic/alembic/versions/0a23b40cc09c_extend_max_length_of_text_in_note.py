"""Extend max length of text in note

Revision ID: 0a23b40cc09c
Revises: 
Create Date: 2024-08-29 11:37:20.827291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String

from database.model.field_length import LONG

# revision identifiers, used by Alembic.
revision: str = "0a23b40cc09c"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "note_organisation",
        "value",
        type_=String(LONG * 4),
    )


def downgrade() -> None:
    pass
