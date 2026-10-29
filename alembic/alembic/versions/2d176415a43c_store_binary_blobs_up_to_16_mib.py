"""Store binary blobs up to 16 MiB

The binary_blob columns were created as BLOB, which holds at most 65,535 bytes on MySQL, while the
image endpoints accept files up to 1 MiB. MEDIUMBLOB holds up to 16 MiB.

Revision ID: 2d176415a43c
Revises: 8f9ac801a283
Create Date: 2026-10-28 18:58:06.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "2d176415a43c"
down_revision: Union[str, None] = "8f9ac801a283"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The same tables as in fabaaad1cf1f, which added the binary_blob columns.
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

assets_with_distributions = [
    "case_study",
    "dataset",
    "experiment",
    "computational_asset",
    "ml_model",
    "publication",
]


def _tables() -> list[str]:
    return [f"media_{asset_type}" for asset_type in assets_with_media] + [
        f"distribution_{asset_type}" for asset_type in assets_with_distributions
    ]


def upgrade() -> None:
    for table in _tables():
        op.alter_column(
            table,
            "binary_blob",
            type_=mysql.MEDIUMBLOB(),
            existing_type=sa.LargeBinary(),
            existing_nullable=True,
        )


def downgrade() -> None:
    # Fails on MySQL, instead of truncating, if a stored blob is longer than 65,535 bytes.
    for table in _tables():
        op.alter_column(
            table,
            "binary_blob",
            type_=sa.LargeBinary(),
            existing_type=mysql.MEDIUMBLOB(),
            existing_nullable=True,
        )
