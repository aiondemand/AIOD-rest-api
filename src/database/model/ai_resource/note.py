from typing import Type

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import Field, SQLModel

from database.model.field_length import DESCRIPTION


class NoteBase(SQLModel):
    value: str = Field(
        index=False,
        unique=False,
        description="The string value",
        max_length=DESCRIPTION,
        schema_extra={"example": "A brief record of points or ideas about this AI resource."},
    )


def note_factory(table_from: str) -> Type:
    class NoteORM(NoteBase, table=True):  # type: ignore [call-arg]
        __tablename__ = f"note_{table_from}"

        identifier: int | None = Field(primary_key=True)
        linked_identifier: int | None = Field(
            sa_column=Column(Integer, ForeignKey(table_from + ".identifier", ondelete="CASCADE"))
        )

    NoteORM.__name__ = NoteORM.__qualname__ = f"note_{table_from}"
    return NoteORM


class Note(NoteBase):
    """Extra textual information about an entity"""
