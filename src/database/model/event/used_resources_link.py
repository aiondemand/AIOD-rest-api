from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import SQLModel, Field


class EventUsedResourcesLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "event_used_resources_link"
    event_identifier: int = Field(
        sa_column=Column(
            Integer, ForeignKey("event.identifier", ondelete="CASCADE"), primary_key=True
        )
    )
    used_resources_identifier: int = Field(
        sa_column=Column(
            Integer, ForeignKey("ai_asset_old.identifier", ondelete="CASCADE"), primary_key=True
        )
    )
