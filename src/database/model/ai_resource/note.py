from sqlmodel import Field

from database.model.named_relation import NamedRelation
from database.model.field_length import DESCRIPTION


class Note(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "note"
    name: str = Field(
        index=False, unique=False, description="The string value", max_length=DESCRIPTION
    )
