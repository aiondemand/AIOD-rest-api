from sqlalchemy import TEXT, Column
from sqlmodel import SQLModel, Field

from database.model import field_length


class TextBase(SQLModel):
    plain: str | None = Field(
        max_length=field_length.MAX_TEXT,
        sa_column=Column(TEXT),
        schema_extra={"example": "Plain text."},
        default=None,
    )
    html: str | None = Field(
        max_length=field_length.MAX_TEXT,
        sa_column=Column(TEXT),
        schema_extra={"example": "<p>Text with <strong>html formatting</strong>.</p>"},
        default=None,
    )


class TextORM(TextBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "text"
    identifier: int = Field(default=None, primary_key=True)


class Text(TextBase):
    """Provide text in different formats. Ideally only one of them is filled, or all fields
    contain the same content with different formatting."""
