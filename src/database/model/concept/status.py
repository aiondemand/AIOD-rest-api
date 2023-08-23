from typing import List
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import SQLModel, Field, Relationship

from database.model.named_relation import NamedRelation

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.concept.aiod_entry import AIoDEntryORM


class AIoDEntryStatusLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "aiod_entry_status_link"

    aiod_entry_identifier: int = Field(
        sa_column=Column(
            Integer, ForeignKey("aiod_entry.identifier", ondelete="CASCADE"), primary_key=True
        )
    )
    alternate_name_identifier: int | None = Field(foreign_key="status.identifier", primary_key=True)


class Status(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "status"

    entries: List["AIoDEntryORM"] = Relationship(
        back_populates="status", link_model=AIoDEntryStatusLink
    )
