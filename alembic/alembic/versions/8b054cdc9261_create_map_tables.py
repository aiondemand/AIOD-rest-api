"""Create Identifier Map Tables

Revision ID: 8b054cdc9261
Revises: 1662d64ebe23
Create Date: 2025-05-14 09:07:47.064937

"""

import logging

# no user input
# ruff: noqa: S608
from typing import Sequence, Union, NamedTuple

from alembic import op
from sqlalchemy import Column, Integer, text, String

# revision identifiers, used by Alembic.
revision: str = "8b054cdc9261"
down_revision: Union[str, None] = "1662d64ebe23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic")


class ParentTable(NamedTuple):
    name: str
    fk_identifier: str
    children: list[str]


def upgrade() -> None:
    # For more information, see docs/developer/schema/index.md#a-note-on-identifiers
    aiod_concept = ParentTable(
        name="aiod_concept",
        fk_identifier="identifier",
        children=[
            "contact",
            "organisation",
            "person",
            "dataset",
            "publication",
            "case_study",
            "computational_asset",
            "experiment",
            "ml_model",
            "educational_resource",
            "event",
            "news",
            "project",
            "service",
            "team",
            "resource_bundle",
        ],
    )
    ai_resource = ParentTable(
        name="ai_resource",
        fk_identifier="ai_resource_id",
        children=[
            "organisation",
            "person",
            "dataset",
            "publication",
            "case_study",
            "computational_asset",
            "experiment",
            "ml_model",
            "educational_resource",
            "event",
            "news",
            "project",
            "service",
            "team",
            "resource_bundle",
        ],
    )
    ai_asset = ParentTable(
        name="ai_asset",
        fk_identifier="ai_asset_id",
        children=[
            "dataset",
            "publication",
            "case_study",
            "computational_asset",
            "experiment",
            "ml_model",
        ],
    )
    agent = ParentTable(
        name="agent",
        fk_identifier="agent_id",
        children=["organisation", "person"],
    )
    abbreviations = {
        "contact": "con",
        "organisation": "org",
        "person": "prsn",
        "dataset": "data",
        "publication": "pub",
        "case_study": "case",
        "computational_asset": "comp",
        "experiment": "exp",
        "ml_model": "mdl",
        "educational_resource": "edu",
        "event": "evnt",
        "news": "news",
        "project": "proj",
        "service": "srvc",
        "team": "team",
        "resource_bundle": "res",
    }

    # We create a function to generate a random sequence
    # We could've gone for UUID also, but it's more verbose and
    # MySQL natively only has UUID1.
    op.execute(
        text(
            """
            CREATE FUNCTION rand_id() RETURNS VARCHAR(24)
            DETERMINISTIC
            BEGIN
                DECLARE chars VARCHAR(62) DEFAULT '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
                DECLARE result VARCHAR(24) DEFAULT '';
                DECLARE i INT DEFAULT 0;
                WHILE i < 24 DO
                    SET result = CONCAT(result, SUBSTRING(chars, FLOOR(1 + RAND() * 62), 1));
                    SET i = i + 1;
                END WHILE;
                RETURN result;
            END;
            """
        )
    )
    # We store a map for the old->new identifiers so we can support backwards compatibility (maybe)
    # For regular identifiers, we store this per concept, as this is how they are likely accessed
    # (e.g., /dataset/1). For parent identifiers we store it all together for parent routers.
    # TODO: Actually generate new identifiers
    for child in aiod_concept.children:
        logger.info(f"Creating conversion table for {child}")
        map_table = f"_{child}_identifier_map"
        op.create_table(
            map_table,
            Column("old", Integer, index=True),
            Column("new", String(30), index=True),
        )
        op.execute(
            f"INSERT INTO {map_table} SELECT identifier, CONCAT('{abbreviations[child]}', '_', rand_id()) FROM {child} "
        )

    for parent in [ai_resource, ai_asset, agent]:
        logger.info(f"Creating conversion table for {parent.name}")
        map_table = f"_{parent.name}_identifier_map"
        op.create_table(
            map_table,
            Column("old", Integer, index=True),
            Column("new", String(30), index=True),
        )
        child_data = "UNION ".join(
            f"SELECT child.{parent.fk_identifier} as parent_identifier, child_map_table.new as new_identifier "
            f"FROM {child_table} as child "
            f"JOIN _{child_table}_identifier_map as child_map_table "
            f"ON child_map_table.old=child.identifier "
            for child_table in parent.children
        )
        op.execute(f"INSERT INTO {map_table} SELECT * FROM ({child_data}) as child")


def downgrade() -> None:
    pass
