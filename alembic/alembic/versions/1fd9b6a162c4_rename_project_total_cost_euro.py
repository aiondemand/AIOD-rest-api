"""rename project total_cost_euro

Revision ID: 1fd9b6a162c4
Revises: fabaaad1cf1f
Create Date: 2025-08-19 08:43:51.774262

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import DECIMAL

# revision identifiers, used by Alembic.
revision: str = "1fd9b6a162c4"
down_revision: Union[str, None] = "fabaaad1cf1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "project",
        "total_cost_euro",
        new_column_name="total_cost_euros",
        existing_type=DECIMAL(12, 2),
        existing_nullable=True,
        existing_server_default=None,
    )


def downgrade() -> None:
    op.alter_column(
        "project",
        "total_cost_euros",
        new_column_name="total_cost_euro",
        existing_type=DECIMAL(12, 2),
        existing_nullable=True,
        existing_server_default=None,
    )
