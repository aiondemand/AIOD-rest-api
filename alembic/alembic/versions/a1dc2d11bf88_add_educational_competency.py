"""add educational competency

Revision ID: a1dc2d11bf88
Revises: d02aac64a5c7
Create Date: 2025-09-25 09:44:35.566898

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1dc2d11bf88"
down_revision: Union[str, None] = "d02aac64a5c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
