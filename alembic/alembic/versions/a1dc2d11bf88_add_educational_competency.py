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
    op.add_column(
        "educational_resource",
        sa.Column("required_competency_level_identifier", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "educational_resource_required_competency_level_ibfk",
        "educational_resource",
        "educational_competency",
        ["required_competency_level_identifier"],
        ["identifier"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "educational_resource_required_competency_level_ibfk",
        "educational_resource",
        type_="foreignkey",
    )
    op.drop_column("educational_resource", "required_competency_level_identifier")
