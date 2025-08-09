"""Add organisation.turnover and organisation.number_of_employees

Revision ID: 5d0d73539c21
Revises: 1662d64ebe23
Create Date: 2025-05-12 14:00:35.644646

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d0d73539c21"
down_revision: Union[str, None] = "751c3f34323a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("organisation", sa.Column("turnover_identifier", sa.Integer(), nullable=True))
    op.add_column(
        "organisation", sa.Column("number_of_employees_identifier", sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        "fk_organisation_turnover_identifier",
        "organisation",
        "turnover",
        ["turnover_identifier"],
        ["identifier"],
    )

    op.create_foreign_key(
        "fk_organisation_number_of_employees_identifier",
        "organisation",
        "number_of_employees",
        ["number_of_employees_identifier"],
        ["identifier"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_organisation_number_of_employees_identifier", "organisation", type_="foreignkey"
    )
    op.drop_constraint("fk_organisation_turnover_identifier", "organisation", type_="foreignkey")

    op.drop_column("organisation", "number_of_employees_identifier")
    op.drop_column("organisation", "turnover_identifier")
