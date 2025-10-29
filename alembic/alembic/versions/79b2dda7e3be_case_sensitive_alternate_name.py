"""Make alternate name case sensitive

Revision ID: 79b2dda7e3be
Revises: 1d53330411fa
Create Date: 2025-10-29 08:14:27.873149

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision: str = "79b2dda7e3be"
down_revision: Union[str, None] = "1d53330411fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE alternate_name DROP CONSTRAINT AlternateName_name_lowercase")
    op.drop_index(index_name="ix_alternate_name_name", table_name="alternate_name")
    op.alter_column(
        table_name="alternate_name",
        column_name="name",
        nullable=True,
        existing_nullable=True,
        default=None,
        existing_server_default=None,
        type_=String(length=1800),
    )


def downgrade() -> None:
    pass
