"""add more taxonomies

Revision ID: 586692ca94e4
Revises: 1fd9b6a162c4
Create Date: 2025-09-08 15:27:09.067620

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, Column, Boolean, Integer

# revision identifiers, used by Alembic.
revision: str = "586692ca94e4"
down_revision: Union[str, None] = "1fd9b6a162c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NORMAL = 256
LONG = 1800
# These classes already existed as NamedRelation tables prior to this update
UPGRADE_TAXONOMY_TABLES = [
    # ("industrial_sector", "IndustrialSector"),
    ("organisation_type", "OrganisationType"),
    ("event_mode", "EventMode"),
    ("event_status", "EventStatus"),
]

# These classes were introduced or existed as something other than a NamedRelation
ADD_TAXONOMY_TABLES = []


def upgrade() -> None:
    description_column = Column("definition", String(LONG), nullable=True)
    official_column = Column("official", Boolean(), nullable=True, default=False)
    parent_id = Column("parent_id", Integer(), nullable=True)
    for table, class_name in TAXONOMY_TABLES:
        for column in [description_column, official_column, parent_id]:
            op.add_column(table_name=table, column=column)

        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {class_name}_name_lowercase")


def downgrade() -> None:
    for table, _ in TAXONOMY_TABLES:
        op.drop_column(table_name=table, column_name="definition")
        op.drop_column(table_name=table, column_name="official")
        op.alter_column(
            table,
            column_name="name",
            type_=String(length=NORMAL),
            existing_nullable=False,
        )
