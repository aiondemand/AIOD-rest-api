"""make content_url optional and add image_blob

Revision ID: fabaaad1cf1f
Revises: 751c3f34323a
Create Date: 2025-07-28 13:00:53.320039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fabaaad1cf1f'
down_revision: Union[str, None] = '751c3f34323a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('media_organisation', 'content_url',
               existing_type=sa.String(length=1800),
               nullable=True)
    op.add_column('media_organisation',
               sa.Column('image_blob', sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.alter_column('media_organisation', 'content_url',
               existing_type=sa.String(length=1800),
               nullable=False)
    op.drop_column('media_organisation', 'image_blob')

