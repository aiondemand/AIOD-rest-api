from sqlmodel import SQLModel, Field

from database.model.field_length import NORMAL


class NamedRelation(SQLModel):
    """An enumerable-type string"""

    identifier: int = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, description="The string value", max_length=NORMAL)
