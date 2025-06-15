import os
from typing import Tuple

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import declared_attr
from sqlmodel import SQLModel, Field

from database.model.field_length import NORMAL

IS_SQLITE = os.getenv("DB") == "SQLite"
CONSTRAINT_LOWERCASE_NAME = f"{'name' if IS_SQLITE else 'BINARY(name)'} = LOWER(name)"


class NamedRelation(SQLModel):
    """An enumerable-type string (lowercase)"""

    identifier: int = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, description="The term or text", max_length=NORMAL)

    @declared_attr
    def __table_args__(cls) -> Tuple:
        return (
            CheckConstraint(
                CONSTRAINT_LOWERCASE_NAME,
                name=f"{cls.__name__}_name_lowercase",
            ),
        )


class Taxonomy(NamedRelation):
    """An extension of named relation which should only allow specific terms in the database."""

    description: str = Field(description="", nullable=True, max_length=NORMAL)
    # 'official' shouldn't be shown to users, but used by the REST API for filtering.
    official: bool = Field(
        default=False, description="This term is part of the official AIoD taxonomy."
    )
    # nb. `official` is a stopgap to support the fact that terms already
    # existed in the database prior to defining the taxonomies. The long-term plan is to evaluate the
    # unofficial terms and map them to official ones or add them to the taxonomy, which results in
    # all terms being official, at which point this can be deleted.
    # If the NamedRelation is not defined in a taxonomy (e.g., e-mail, alias), then this term can be
    # ignored.
