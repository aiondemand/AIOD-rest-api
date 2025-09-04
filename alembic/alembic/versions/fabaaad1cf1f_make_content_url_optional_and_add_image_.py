"""make content_url optional and add image_blob

Revision ID: fabaaad1cf1f
Revises: 751c3f34323a
Create Date: 2025-07-28 13:00:53.320039

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fabaaad1cf1f"
down_revision: Union[str, None] = "5d0d73539c21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

assets_with_media = [
    "case_study",
    "computational_asset",
    "dataset",
    "educational_resource",
    "event",
    "experiment",
    "ml_model",
    "news",
    "organisation",
    "person",
    "project",
    "publication",
    "resource_bundle",
    "service",
    "team",
]


def upgrade() -> None:
    for asset_type in assets_with_media:
        op.alter_column(
            f"media_{asset_type}",
            "content_url",
            existing_type=sa.String(length=1800),
            nullable=True,
        )

        op.add_column(
            table_name=f"media_{asset_type}",
            column=sa.Column("binary_blob", sa.LargeBinary(), nullable=True),
        )


def downgrade() -> None:
    for asset_type in assets_with_media:
        op.alter_column(
            f"media_{asset_type}",
            "content_url",
            existing_type=sa.String(length=1800),
            nullable=False,
        )

        op.drop_column(f"media_{asset_type}", "binary_blob")
