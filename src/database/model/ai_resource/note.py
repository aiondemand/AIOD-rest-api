from typing import Type

from pydantic import create_model
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlmodel import Field, SQLModel

from database.model.field_length import VERY_LONG
from database.model.field_length import IDENTIFIER_LENGTH


class NoteBase(SQLModel):
    value: str = Field(
        index=False,
        unique=False,
        description="The string value",
        max_length=VERY_LONG,
        schema_extra={"example": "A brief record of points or ideas about this AI resource."},
    )


def note_factory(table_from: str) -> Type:
    NoteORM = create_model(
        f"note_{table_from}",
        __base__=(NoteBase,),
        __cls_kwargs__=dict(table=True),
        identifier=(int | None, Field(primary_key=True)),
        linked_identifier=(
            str | None,
            Field(
                sa_column=Column(
                    String(IDENTIFIER_LENGTH),
                    ForeignKey(table_from + ".identifier", ondelete="CASCADE"),
                )
            ),
        ),
    )
    # Pydantic will issue a warning for non-default dunder attributes, so we add it after creation
    NoteORM.__tablename__ = f"note_{table_from}"
    return NoteORM


class Note(NoteBase):
    """Extra textual information about an entity"""
