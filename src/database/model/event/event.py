from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship

from database.model.agent.agent_table import AgentTable
from database.model.ai_resource.resource import AIResourceBase, AIResource
from database.model.event.event_mode import EventMode
from database.model.event.event_status import EventStatus
from database.model.field_length import NORMAL, DESCRIPTION
from database.model.helper_functions import link_factory
from database.model.relationships import ResourceRelationshipList, ResourceRelationshipSingle
from database.model.serializers import (
    AttributeSerializer,
    FindByIdentifierDeserializer,
    FindByNameDeserializer,
)


class EventBase(AIResourceBase):
    start_date: datetime = Field(
        description="The start date and time of the event, formatted using the ISO 8601 date-time "
        "format.",
        default=None,
        schema_extra={"example": "2021-02-03T15:15:00"},
    )
    end_date: datetime | None = Field(
        description="The end date and time of the event, formatted using the ISO 8601 date-time "
        "format.",
        default=None,
        schema_extra={"example": "2022-01-01T15:15:00"},
    )
    schedule: str | None = Field(
        description="The agenda of the event.",
        max_length=DESCRIPTION,
        default=None,
        schema_extra={"example": "10:00-10:30: Opening. 10:30-11:00 ..."},
    )
    registration_link: str | None = Field(
        description="The url of the registration form.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "https://example.com/registration-form"},
    )
    # Did not add duration here: it can be described using start_date and end_date


class Event(EventBase, AIResource, table=True):  # type: ignore [call-arg]
    __tablename__ = "event"

    performer: list["AgentTable"] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"},
        link_model=link_factory("event", AgentTable.__tablename__, table_prefix="performer"),
    )
    organiser_identifier: int | None = Field(foreign_key=AgentTable.__tablename__ + ".identifier")
    organiser: Optional[AgentTable] = Relationship()
    status_identifier: int | None = Field(foreign_key=EventStatus.__tablename__ + ".identifier")
    status: Optional[EventStatus] = Relationship()
    mode_identifier: int | None = Field(foreign_key=EventMode.__tablename__ + ".identifier")
    mode: Optional[EventMode] = Relationship()

    class RelationshipConfig(AIResource.RelationshipConfig):
        performer: list[int] = ResourceRelationshipList(
            description="Links to identifiers of the agents (person or organization) that is "
            "contributing to this event ",
            serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializer(AgentTable),
            default_factory_pydantic=list,
            example=[],
        )
        organiser: Optional[int] = ResourceRelationshipSingle(
            identifier_name="organiser_identifier",
            description="The person or organisation responsible for organising the event.",
            serializer=AttributeSerializer("identifier"),
        )
        status: Optional[str] = ResourceRelationshipSingle(
            description="The status of the event.",
            identifier_name="status_identifier",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(EventStatus),
            example="scheduled",
        )
        mode: Optional[str] = ResourceRelationshipSingle(
            description="The attendance mode of event.",
            identifier_name="mode_identifier",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(EventMode),
            example="offline",
        )
