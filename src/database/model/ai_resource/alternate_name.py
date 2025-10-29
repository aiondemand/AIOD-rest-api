from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel

from database.model.field_length import LONG


class AlternateName(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "alternate_name"

    identifier: int = Field(default=None, primary_key=True)
    name: str = Field(
        sa_column=Column(String(length=LONG)),
        description="The term or text",
    )
