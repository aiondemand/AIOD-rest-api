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
    name: str = Field(index=True, unique=True, description="The string value", max_length=NORMAL)

    @declared_attr
    def __table_args__(cls) -> Tuple:
        return (
            CheckConstraint(
                CONSTRAINT_LOWERCASE_NAME,
                name=f"{cls.__name__}_name_lowercase",
            ),
        )
