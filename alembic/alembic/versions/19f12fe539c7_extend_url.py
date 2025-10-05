"""extend-url

Revision ID: 19f12fe539c7
Revises: eb4e8cf555d9
Create Date: 2025-10-05 06:14:48.308493

"""

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String

logger = logging.getLogger("alembic")

# revision identifiers, used by Alembic.
revision: str = "19f12fe539c7"
down_revision: Union[str, None] = "eb4e8cf555d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    logger.info("Removing check constraint")
    op.drop_constraint(
        constraint_name="RelevantLink_name_lowercase",
        table_name="relevant_link",
        type_="check",
    )
    logger.info("Removing unique constraint")
    op.drop_constraint(
        constraint_name="ix_relevant_link_name",
        table_name="relevant_link",
        type_="unique",
    )
    logger.info("Updating Column")
    op.alter_column(
        table_name="relevant_link",
        column_name="name",
        type_=String(length=2000),
        existing_nullable=True,
        existing_server_default=None,
    )


def downgrade() -> None:
    pass
