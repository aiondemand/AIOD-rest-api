"""add documented_in relationship to AIResource

Revision ID: 4uf1v7ujjkuq
Revises: a1dc2d11bf88
Create Date: 2025-11-25 15:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4uf1v7ujjkuq"
down_revision: Union[str, None] = "a1dc2d11bf88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# All non-abstract AIResource subclasses
AI_RESOURCE_TABLES = [
    "dataset",
    "publication",
    "case_study",
    "computational_asset",
    "experiment",
    "ml_model",
    "educational_resource",
    "event",
    "news",
    "project",
    "service",
    "organisation",
    "person",
    "team",
    "resource_bundle",
]


def upgrade() -> None:
    """
    Create link tables for the documented_in relationship between AIResource subclasses
    and KnowledgeAsset.
    """
    for table_name in AI_RESOURCE_TABLES:
        link_table_name = f"documented_in_{table_name}_knowledge_asset_link"

        op.create_table(
            link_table_name,
            sa.Column("from_identifier", sa.String(30), nullable=False),
            sa.Column("linked_identifier", sa.String(30), nullable=False),
            sa.PrimaryKeyConstraint("from_identifier", "linked_identifier"),
            sa.ForeignKeyConstraint(
                ["from_identifier"],
                [f"{table_name}.identifier"],
                name=f"{link_table_name}_ibfk_1",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["linked_identifier"],
                ["knowledge_asset.identifier"],
                name=f"{link_table_name}_ibfk_2",
                onupdate="CASCADE",
            ),
        )

        # Create indexes for better query performance
        op.create_index(f"ix_{link_table_name}_from", link_table_name, ["from_identifier"])
        op.create_index(f"ix_{link_table_name}_linked", link_table_name, ["linked_identifier"])


def downgrade() -> None:
    """
    Drop all documented_in link tables.
    """
    for table_name in AI_RESOURCE_TABLES:
        link_table_name = f"documented_in_{table_name}_knowledge_asset_link"
        op.drop_table(link_table_name)
