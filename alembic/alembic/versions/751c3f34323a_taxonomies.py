"""Adds `description` and `official` columns to taxonomy tables

Revision ID: 751c3f34323a
Revises: 459323683348
Create Date: 2025-06-15 09:07:21.057214

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import Column, String, Boolean

from database.model.field_length import NORMAL

# revision identifiers, used by Alembic.
revision: str = "751c3f34323a"
down_revision: Union[str, None] = "459323683348"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TAXONOMY_TABLES = [
    "industrial_sector",
    "license",
    "news_category",
    "publication_type",
    "research_area",
    "scientific_domain",
]


def upgrade() -> None:
    description_column = Column("definition", String(NORMAL), nullable=True)
    official_column = Column("official", Boolean(), nullable=True, default=False)
    for table in TAXONOMY_TABLES:
        for column in [description_column, official_column]:
            op.add_column(table_name=table, column=column)


def downgrade() -> None:
    for table in TAXONOMY_TABLES:
        op.drop_column(table_name=table, column_name="definition")
        op.drop_column(table_name=table, column_name="official")
