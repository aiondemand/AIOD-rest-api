"""Adds `description`, `official`, and `parent_id` columns to taxonomy tables

Revision ID: 751c3f34323a
Revises: 459323683348
Create Date: 2025-06-15 09:07:21.057214

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import Column, String, Boolean, Integer

from database.model.field_length import NORMAL, LONG

# revision identifiers, used by Alembic.
revision: str = "751c3f34323a"
down_revision: Union[str, None] = "42f747800456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TAXONOMY_TABLES = [
    ("industrial_sector", "IndustrialSector"),
    ("license", "License"),
    ("news_category", "NewsCategory"),
    ("publication_type", "PublicationType"),
    ("research_area", "ResearchArea"),
    ("scientific_domain", "ScientificDomain"),
]


def upgrade() -> None:
    description_column = Column("definition", String(LONG), nullable=True)
    official_column = Column("official", Boolean(), nullable=True, default=False)
    parent_id = Column("parent_id", Integer(), nullable=True)
    for table, class_name in TAXONOMY_TABLES:
        for column in [description_column, official_column, parent_id]:
            op.add_column(table_name=table, column=column)

        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {class_name}_name_lowercase")


def downgrade() -> None:
    for table in TAXONOMY_TABLES:
        op.drop_column(table_name=table, column_name="definition")
        op.drop_column(table_name=table, column_name="official")
        op.alter_column(
            table,
            column_name="name",
            type_=String(length=NORMAL),
            existing_nullable=False,
        )
