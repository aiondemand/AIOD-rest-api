"""Extend description length

Revision ID: 279e17c48ea1
Revises: 0a23b40cc09c
Create Date: 2024-10-29 14:38:30.684251

"""
from typing import Sequence, Union

from alembic import op

from sqlalchemy import String

from database.model.field_length import LONG

# revision identifiers, used by Alembic.
revision: str = "279e17c48ea1"
down_revision: Union[str, None] = "0a23b40cc09c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All models that have associated distributions
    for table in [
        "dataset",
        "case_study",
        "publication",
        "computational_asset",
        "ml_model",
        "experiment",
    ]:
        op.alter_column(
            f"distribution_{table}",
            "content_url",
            type_=String(LONG),
        )


def downgrade() -> None:
    # from NORMAL
    pass
