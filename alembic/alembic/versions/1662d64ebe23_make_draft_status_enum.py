"""make draft status enum

Revision ID: 1662d64ebe23
Revises: d09ed8ad4533
Create Date: 2024-12-17 09:02:30.480835

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import Column, INT, String, Enum

from database.model.field_length import NORMAL
from database.model.concept.aiod_entry import EntryStatus

# revision identifiers, used by Alembic.
revision: str = "1662d64ebe23"
down_revision: Union[str, None] = "d09ed8ad4533"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("aiod_entry_status_link")
    op.add_column(
        "aiod_entry",
        Column("status", Enum(EntryStatus)),
    )
    op.execute(
        """
        UPDATE aiod_entry
        INNER JOIN status
        ON status.identifier = aiod_entry.status_identifier
        SET aiod_entry.status = status.name
        """
    )
    op.drop_constraint(
        constraint_name="aiod_entry_ibfk_1",
        table_name="aiod_entry",
        type_="foreignkey",
    )
    op.drop_column(
        table_name="aiod_entry",
        column_name="status_identifier",
    )
    op.drop_table("status")


def downgrade() -> None:
    # No need to recreate table status link, it was not used.
    op.create_table(
        "status",
        Column("identifier", type_=INT, primary_key=True),
        Column(
            "name",
            unique=True,
            type_=String(NORMAL),
            index=True,
        ),
    )
    op.execute(
        """
        INSERT INTO status
        VALUES (1, 'draft'), (2, 'published'), (3, 'rejected'), (4, 'submitted')
        """
    )
    op.add_column(
        "aiod_entry",
        Column("status_identifier", INT),
    )
    op.execute(
        """
        UPDATE aiod_entry
        INNER JOIN status
        ON aiod_entry.status = status.name
        SET aiod_entry.status_identifier = status.identifier
        """
    )
    op.drop_column(
        "aiod_entry",
        "status",
    )
    op.create_foreign_key(
        "aiod_entry_ibfk_1",
        "aiod_entry",
        "status",
        ["status_identifier"],
        ["identifier"],
    )
