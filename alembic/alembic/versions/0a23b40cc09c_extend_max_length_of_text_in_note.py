"""Extend max length of text in note

Revision ID: 0a23b40cc09c
Revises: 
Create Date: 2024-08-29 11:37:20.827291

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import String

from database.model.field_length import VERY_LONG

# revision identifiers, used by Alembic.
revision: str = "0a23b40cc09c"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All models that derive from AIResourceBase
    for table in [
        "news",
        "team",
        "person",
        "organisation",
        "event",
        "project",
        "service",
        "dataset",
        "case_study",
        "publication",
        "computational_asset",
        "ml_model",
        "experiment",
        "educational_resource",
    ]:
        op.alter_column(
            f"note_{table}",
            "value",
            type_=String(VERY_LONG),
        )


def downgrade() -> None:
    pass
