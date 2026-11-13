"""add pricing, applies, solution and approach to AIAsset

Revision ID: 9k2m4n6p8q0r
Revises: 8f9ac801a283
Create Date: 2025-11-25 17:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9k2m4n6p8q0r"
down_revision: Union[str, None] = "8f9ac801a283"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# AIAsset subclass table names
AI_ASSET_TABLES = [
    "dataset",
    "ml_model",
    "experiment",
    "computational_asset",
    "case_study",
    "publication",
]


def upgrade() -> None:
    """
    1. Create solution and approach taxonomy tables
    2. Add pricing_info and applies_to fields to AIAsset base tables
    3. Create link tables for solution and approach many-to-many relationships
    """
    # Create solution taxonomy table
    op.create_table(
        "solution",
        sa.Column("identifier", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("definition", sa.String(2000), nullable=True),
        sa.Column("official", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("identifier"),
        sa.ForeignKeyConstraint(["parent_id"], ["solution.identifier"]),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_solution_name", "solution", ["name"])

    # Create approach taxonomy table
    op.create_table(
        "approach",
        sa.Column("identifier", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("definition", sa.String(2000), nullable=True),
        sa.Column("official", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("identifier"),
        sa.ForeignKeyConstraint(["parent_id"], ["approach.identifier"]),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_approach_name", "approach", ["name"])

    # Add pricing_info and applies_to columns to each AIAsset subclass table
    for table_name in AI_ASSET_TABLES:
        op.add_column(table_name, sa.Column("pricing_info", sa.String(200), nullable=True))
        op.add_column(table_name, sa.Column("applies_to", sa.String(200), nullable=True))

    # Create link tables for solution many-to-many relationship
    for table_name in AI_ASSET_TABLES:
        link_table_name = f"solution_{table_name}_link"
        op.create_table(
            link_table_name,
            sa.Column("from_identifier", sa.String(30), nullable=False),
            sa.Column("linked_identifier", sa.Integer(), nullable=False),
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
                ["solution.identifier"],
                name=f"{link_table_name}_ibfk_2",
                onupdate="CASCADE",
            ),
        )
        op.create_index(f"ix_{link_table_name}_from", link_table_name, ["from_identifier"])
        op.create_index(f"ix_{link_table_name}_linked", link_table_name, ["linked_identifier"])

    # Create link tables for approach many-to-many relationship
    for table_name in AI_ASSET_TABLES:
        link_table_name = f"approach_{table_name}_link"
        op.create_table(
            link_table_name,
            sa.Column("from_identifier", sa.String(30), nullable=False),
            sa.Column("linked_identifier", sa.Integer(), nullable=False),
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
                ["approach.identifier"],
                name=f"{link_table_name}_ibfk_2",
                onupdate="CASCADE",
            ),
        )
        op.create_index(f"ix_{link_table_name}_from", link_table_name, ["from_identifier"])
        op.create_index(f"ix_{link_table_name}_linked", link_table_name, ["linked_identifier"])


def downgrade() -> None:
    """
    Reverse all changes from upgrade()
    """
    # Drop approach link tables
    for table_name in AI_ASSET_TABLES:
        op.drop_table(f"approach_{table_name}_link")

    # Drop solution link tables
    for table_name in AI_ASSET_TABLES:
        op.drop_table(f"solution_{table_name}_link")

    # Remove pricing_info and applies_to columns
    for table_name in AI_ASSET_TABLES:
        op.drop_column(table_name, "applies_to")
        op.drop_column(table_name, "pricing_info")

    # Drop taxonomy tables
    op.drop_table("approach")
    op.drop_table("solution")
