"""Add new columns to computationalasset

Revision ID: 3c81fb00d65e
Revises: 0f2fe1324047
Create Date: 2024-12-09 11:08:11.995793

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import String, Column, Integer, ForeignKey, inspect
from database.model.field_length import NORMAL

# revision identifiers, used by Alembic.
revision: str = "3c81fb00d65e"
down_revision: Union[str, None] = "0f2fe1324047"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        f"computational_asset",
        Column("os", String(NORMAL)),
    )
    op.add_column(
        f"computational_asset",
        Column("kernel", String(NORMAL)),
    )
    op.add_column(
        f"computational_asset",
        Column("pricing_scheme", String(NORMAL)),
    )
    op.add_column(
        "location",
        Column(
            "computational_asset_identifier",
            Integer,
            ForeignKey("computational_asset.identifier", ondelete="CASCADE"),
        ),
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    location_columns = inspector.get_columns("location")
    column_names = [col["name"] for col in location_columns]

    if "computational_asset_identifier" in column_names:
        foreign_keys = inspector.get_foreign_keys("location")
        for fk in foreign_keys:
            if "computational_asset_identifier" in fk["constrained_columns"]:
                print(f"Dropping constraint: {fk['name']}")
                op.drop_constraint(fk["name"], "location", type_="foreignkey")

        op.drop_column("location", "computational_asset_identifier")

    comp_columns = inspector.get_columns("computational_asset")
    comp_column_names = [col["name"] for col in comp_columns]

    for col in ["pricing_scheme", "kernel", "os"]:
        if col in comp_column_names:
            print(f"Dropping column {col}")
            op.drop_column("computational_asset", col)
