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
    ("organisation_type", "OrganisationType"),
    ("event_mode", "EventMode"),
    ("event_status", "EventStatus"),
    ("language", "Language"),
    ("educational_level", "EducationalLevel"),
]

# These classes were introduced or existed as something other than a NamedRelation
ADD_TAXONOMY_TABLES = [
    "educational_competency",
    "learning_mode",
    "organisation_activity_type",
    "country",
]


def upgrade() -> None:
    op.rename_table("edu_educational_level", "educational_level")
    op.rename_table(
        "educational_resource_edu_educational_level_link",
        "educational_resource_educational_level_link",
    )

    description_column = Column("definition", String(LONG), nullable=True)
    official_column = Column("official", Boolean(), nullable=True, default=False)
    parent_id = Column("parent_id", Integer(), nullable=True)

    for table, class_name in UPGRADE_TAXONOMY_TABLES:
        for column in [description_column, official_column, parent_id]:
            op.add_column(table_name=table, column=column)
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {class_name}_name_lowercase")

    for table_name in ADD_TAXONOMY_TABLES:
        op.create_table(
            table_name,
            sa.Column(
                "identifier", sa.Integer, primary_key=True, autoincrement=True, nullable=False
            ),
            sa.Column("name", sa.String(NORMAL), nullable=True),
            sa.Column("definition", sa.String(LONG), nullable=True),
            sa.Column("official", sa.Boolean, nullable=False),
            sa.Column("parent_id", sa.Integer, nullable=True),
            sa.UniqueConstraint("name", name=f"ix_{table_name}_name"),
            sa.ForeignKeyConstraint(
                ["parent_id"], [f"{table_name}.identifier"], name=f"{table_name}_ibfk_1"
            ),
        )
        op.create_index("parent_id", table_name, ["parent_id"])


def downgrade() -> None:
    op.rename_table("educational_level", "edu_educational_level")

    for table, _ in UPGRADE_TAXONOMY_TABLES:
        op.drop_column(table_name=table, column_name="definition")
        op.drop_column(table_name=table, column_name="official")
        op.alter_column(
            table,
            column_name="name",
            type_=String(length=NORMAL),
            existing_nullable=False,
        )

    for table in ADD_TAXONOMY_TABLES:
        op.drop_table(table)
