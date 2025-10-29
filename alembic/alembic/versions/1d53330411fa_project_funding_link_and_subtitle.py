"""Add funding link and subtitle fields to Project

Revision ID: 1d53330411fa
Revises: 19f12fe539c7
Create Date: 2025-10-29 08:04:04.437011

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String

# revision identifiers, used by Alembic.
revision: str = "1d53330411fa"
down_revision: Union[str, None] = "19f12fe539c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for field in ["funding_link", "subtitle"]:
        op.add_column(
            table_name="project",
            column=Column(
                name=field,
                type_=String(length=1800),
                default=None,
                nullable=True,
            ),
        )


def downgrade() -> None:
    for field in ["funding_link", "subtitle"]:
        op.drop_column("project", field)
