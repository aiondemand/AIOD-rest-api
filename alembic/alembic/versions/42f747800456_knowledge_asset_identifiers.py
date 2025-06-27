"""knowledge_asset_identifiers

Revision ID: 42f747800456
Revises: 459323683348
Create Date: 2025-06-24 13:05:59.728619

"""

import logging

# no user input
# ruff: noqa: S608
from typing import Sequence, Union, NamedTuple

from alembic import op
from sqlalchemy import text

from database.session import DbSession


# revision identifiers, used by Alembic.
revision: str = "42f747800456"
down_revision: Union[str, None] = "459323683348"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic")


class ParentTable(NamedTuple):
    name: str
    fk_identifier: str
    children: list[str]


def upgrade() -> None:
    # Simply forgot to update knowledge asset identifiers last time.
    # This script follows the same setup as the last, but only applies to knowledge asset,
    # which at this point only has `publication` as a child referencing it.

    # Fetch foreign key constraints so we can drop them and add them back later.
    with DbSession() as session:
        logger.info("Fetching existing foreign key constraints.")
        constraints = session.execute(
            text(
                "SELECT refs.CONSTRAINT_NAME, refs.DELETE_RULE, kcu.TABLE_NAME, kcu.COLUMN_NAME, kcu.REFERENCED_TABLE_NAME, kcu.REFERENCED_COLUMN_NAME "
                "FROM information_schema.REFERENTIAL_CONSTRAINTS as refs "
                "JOIN information_schema.KEY_COLUMN_USAGE as kcu "
                "ON refs.CONSTRAINT_NAME=kcu.CONSTRAINT_NAME "
                f"WHERE refs.REFERENCED_TABLE_NAME='knowledge_asset';"
            )
        )
    constraints = list(constraints)
    logger.info(f"Dropping {len(constraints)} foreign key constraints.")
    for constraint, delete_rule, from_table, from_column, to_table, to_column in constraints:
        op.execute(f"ALTER TABLE {from_table} DROP FOREIGN KEY {constraint}")

    # Without the foreign key constraints in place, we can update the columns.
    updated_columns = set()
    for constraint, delete_rule, from_table, from_column, to_table, to_column in constraints:
        for table, column in [(to_table, to_column), (from_table, from_column)]:
            if (table, column) not in updated_columns:
                logger.info(f"Altering {table}.{column} to VARCHAR(30) COLLATE utf8_bin.")
                op.execute(
                    f"ALTER TABLE {table} CHANGE COLUMN {column} {column} VARCHAR(30) COLLATE utf8_bin;"
                )
                updated_columns.add((table, column))

    for constraint, delete_rule, from_table, from_column, to_table, to_column in constraints:
        logger.info(f"Adding back constraint {constraint}.")
        op.execute(
            f"ALTER TABLE {from_table} "
            f"ADD CONSTRAINT {constraint} "
            f"FOREIGN KEY ({from_column}) REFERENCES {to_table}({to_column}) "
            f"ON DELETE {delete_rule} "
            f"ON UPDATE CASCADE;"
        )

    # There was a bug which resulted in knowledge asset identifiers not being generated
    logger.info("Creating Identifiers of Knowledge Assets")
    op.execute("INSERT INTO knowledge_asset SELECT identifier, 'publication' FROM publication; ")
    logger.info("Link publications to their parents")
    op.execute("UPDATE publication SET knowledge_asset_id=identifier; ")


def downgrade() -> None:
    pass
