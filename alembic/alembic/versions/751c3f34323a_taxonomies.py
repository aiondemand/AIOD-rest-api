"""Adds `description` and `official` columns to taxonomy tables

Revision ID: 751c3f34323a
Revises: 1662d64ebe23
Create Date: 2025-06-15 09:07:21.057214

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import Column, String, Boolean

from database.model.field_length import NORMAL

# revision identifiers, used by Alembic.
revision: str = "751c3f34323a"
down_revision: Union[str, None] = "1662d64ebe23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    taxonomy_tables = [
        "scientific_domain",
        "research_area",
        "industrial_sector",
        "application_area",
    ]
    description_column = Column("description", String(NORMAL), nullable=True)
    official_column = Column("official", Boolean(), nullable=True, default=False)
    for table in taxonomy_tables:
        for column in [description_column, official_column]:
            op.add_column(table_name=table, column=column)


def downgrade() -> None:
    taxonomy_tables = [
        "scientific_domain",
        "research_area",
        "industrial_sector",
        "application_area",
    ]
    for table in taxonomy_tables:
        op.drop_column(table_name=table, column_name="description")
        op.drop_column(table_name=table, column_name="official")
