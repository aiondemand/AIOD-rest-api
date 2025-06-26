import os
from typing import Tuple, ForwardRef, List

from pydantic import create_model
from sqlalchemy import CheckConstraint, Column, String
from sqlalchemy.orm import declared_attr, backref
from sqlmodel import SQLModel, Field, Relationship

from database.model.field_length import NORMAL, LONG

IS_SQLITE = os.getenv("DB") == "SQLite"
CONSTRAINT_LOWERCASE_NAME = f"{'name' if IS_SQLITE else 'BINARY(name)'} = LOWER(name)"
COLLATION = "NOCASE" if IS_SQLITE else None  # MySQL by default is case insensitive


class NamedRelation(SQLModel):
    """An enumerable-type string (lowercase)"""

    identifier: int = Field(default=None, primary_key=True)
    name: str = Field(
        sa_column=Column(
            String(length=NORMAL, collation=COLLATION),
            index=True,
            unique=True,
        ),
        description="The term or text",
    )

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

    definition: str = Field(description="The meaning of the term.", nullable=True, max_length=LONG)
    # 'official' shouldn't be shown to users, but used by the REST API for filtering.
    official: bool = Field(
        default=False,
        description="If true, indicates this term is part of the official AIoD taxonomy.",
    )
    # nb. `official` is a stopgap to support the fact that terms already
    # existed in the database prior to defining the taxonomies. The long-term plan is to evaluate the
    # unofficial terms and map them to official ones or add them to the taxonomy, which results in
    # all terms being official, at which point this can be deleted.

    @declared_attr
    def __table_args__(cls) -> Tuple:
        # `NamedRelation` would enforce lower-case to help normalize,
        # which we do not want for predefined terms as we assume capitalization to be correct.
        return tuple()


def create_taxonomy(class_name: str, table_name: str) -> type[Taxonomy]:
    clazz = create_model(
        __model_name=class_name,
        __base__=Taxonomy,
        __cls_kwargs__=dict(table=True),
        __tablename__=(str, table_name),
        # Taxonomies are hierarchical, e.g., a Cow is also a Mammal.
        # These fields are updated dynamically in `__init__subclass__`.
        parent_id=(
            int | None,
            Field(foreign_key=f"{table_name}.identifier", default=None, nullable=True),
        ),
        children=(
            List[ForwardRef(class_name)],  # type: ignore
            Relationship(
                sa_relationship_kwargs=dict(
                    cascade="all",
                    backref=backref("parent", remote_side=f"{class_name}.identifier"),
                )
            ),
        ),
    )
    # a `parent: Self | None` attribute is automatically generated based on `children`.
    return clazz
