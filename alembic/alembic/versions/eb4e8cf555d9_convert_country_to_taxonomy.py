"""convert country to taxonomy

Revision ID: eb4e8cf555d9
Revises: a1dc2d11bf88
Create Date: 2025-09-25 09:44:51.192439

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "eb4e8cf555d9"
down_revision: Union[str, None] = "a1dc2d11bf88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
