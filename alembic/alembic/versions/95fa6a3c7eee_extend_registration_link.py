"""extend registration link

Revision ID: 95fa6a3c7eee

Revises: 79b2dda7e3be
Create Date: 2025-10-30 08:30:38.564333

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision: str = "95fa6a3c7eee"
down_revision: Union[str, None] = "79b2dda7e3be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        f"event",
        "registration_link",
        type_=String(1800),
    )


def downgrade() -> None:
    op.alter_column(
        f"event",
        "registration_link",
        type_=String(256),
    )
