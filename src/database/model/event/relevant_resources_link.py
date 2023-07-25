from sqlalchemy import Integer, ForeignKey, Column
from sqlmodel import SQLModel, Field


class EventRelevantResourcesLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "event_relevant_resources_link"
    event_identifier: int = Field(
        sa_column=Column(
            Integer, ForeignKey("event.identifier", ondelete="CASCADE"), primary_key=True
        )
    )
    relevant_resources_identifier: int = Field(
        sa_column=Column(
            Integer, ForeignKey("ai_asset_old.identifier", ondelete="CASCADE"), primary_key=True
        )
    )
