from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship

from database.model.agent.agent_table import AgentTable
from database.model.agent.location import LocationORM, Location
from database.model.ai_resource.resource import AIResourceBase, AbstractAIResource
from database.model.ai_resource.text import TextORM, Text
from database.model.event.event_mode import EventMode
from database.model.event.event_status import EventStatus
from database.model.field_length import NORMAL, LONG
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToMany, ManyToOne, OneToMany, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    FindByNameDeserializer,
    CastDeserializer,
    CastDeserializerList,
    FindByIdentifierDeserializerList,
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
        max_length=LONG,
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


class Event(EventBase, AbstractAIResource, table=True):  # type: ignore [call-arg]
    __tablename__ = "event"

    content_identifier: int | None = Field(
        index=True,
        foreign_key="text.identifier",
        description="Alternative for using .distributions[*].content_url, to make it easier to add "
        "textual content. ",
    )
    content: TextORM | None = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[Event.content_identifier]")
    )
    location: list[LocationORM] = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    performer: list["AgentTable"] = Relationship(
        link_model=many_to_many_link_factory(
            "event", AgentTable.__tablename__, table_prefix="performer"
        ),
    )
    organiser_identifier: int | None = Field(foreign_key=AgentTable.__tablename__ + ".identifier")
    organiser: Optional[AgentTable] = Relationship()
    status_identifier: int | None = Field(foreign_key=EventStatus.__tablename__ + ".identifier")
    status: Optional[EventStatus] = Relationship()
    mode_identifier: int | None = Field(foreign_key=EventMode.__tablename__ + ".identifier")
    mode: Optional[EventMode] = Relationship()

    class RelationshipConfig(AbstractAIResource.RelationshipConfig):
        content: Optional[Text] = OneToOne(
            deserializer=CastDeserializer(TextORM),
            on_delete_trigger_deletion_by="content_identifier",
        )
        location: list[Location] = OneToMany(
            deserializer=CastDeserializerList(LocationORM),
            default_factory_pydantic=list,
        )
        performer: list[int] = ManyToMany(
            description="Links to identifiers of the agents (person or organization) that is "
            "contributing to this event ",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(AgentTable),
            default_factory_pydantic=list,
            example=[],
        )
        organiser: Optional[int] = ManyToOne(
            identifier_name="organiser_identifier",
            description="The person or organisation responsible for organising the event.",
            _serializer=AttributeSerializer("identifier"),
        )
        status: Optional[str] = ManyToOne(
            description="The status of the event.",
            identifier_name="status_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(EventStatus),
            example="scheduled",
        )
        mode: Optional[str] = ManyToOne(
            description="The attendance mode of event.",
            identifier_name="mode_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(EventMode),
            example="offline",
        )
