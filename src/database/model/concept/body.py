from sqlalchemy import Column, TEXT
from sqlmodel import SQLModel, Field


class BodyBase(SQLModel):
    plain: str = Field(
        sa_column=Column(TEXT),  # TODO: this is very slow for Pytest
        description="Plain text content of an entity. Please ",
    )
    html: str = Field(sa_column=Column(TEXT))


class Body(BodyBase, table=True):  # type: ignore [call-arg]
    """The content of an object. Ideally, this"""

    __tablename__ = "body"

    identifier: int = Field(default=None, primary_key=True)
