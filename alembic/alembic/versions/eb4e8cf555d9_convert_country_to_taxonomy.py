"""convert country to taxonomy

Revision ID: eb4e8cf555d9
Revises: a1dc2d11bf88
Create Date: 2025-09-25 09:44:51.192439

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column

# revision identifiers, used by Alembic.
revision: str = "eb4e8cf555d9"
down_revision: Union[str, None] = "a1dc2d11bf88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migrate existing countries to country table as unofficial
    op.execute(
        "insert into country(name, definition, official) SELECT distinct(country), '', false from address;"
    )
    # Create new column that references the identifier
    op.add_column("address", Column("country_identifier", sa.Integer(), nullable=True))

    op.execute(
        "update address a join country c on a.country=c.name set a.country_identifier=c.identifier;"
    )

    op.create_foreign_key(
        "address_country_identifier_ibfk",
        "address",
        "country",
        ["country_identifier"],
        ["identifier"],
    )
    op.drop_column("address", "country")


def downgrade() -> None:
    pass
    # cannot go back since the country constraint is current 3 characters
