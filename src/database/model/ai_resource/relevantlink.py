from sqlmodel import SQLModel, Field

from database.model.field_length import NORMAL


class RelevantLink(SQLModel, table=True):
    """An address of a resource on the web"""

    __tablename__ = "relevant_link"

    identifier: int = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, description="The string value", max_length=NORMAL)
