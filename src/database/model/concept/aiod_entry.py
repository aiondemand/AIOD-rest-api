from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from database.model.concept.status import Status
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToOne, ManyToMany
from database.model.serializers import (
    AttributeSerializer,
    create_getter_dict,
    FindByNameDeserializer,
)

if TYPE_CHECKING:
    from database.model.agent.person import Person
    from authentication import User


class AIoDEntryBase(SQLModel):
    """Metadata of the metadata: when was the metadata last updated, with what identifiers is it
    known on other platforms, etc."""


class AIoDEntryORM(AIoDEntryBase, table=True):  # type: ignore [call-arg]
    """Metadata of the metadata: when was the metadata last updated, with what identifiers is it
    known on other platforms, etc."""

    __tablename__ = "aiod_entry"

    identifier: int = Field(default=None, primary_key=True)
    editor: list["Person"] = Relationship(
        link_model=many_to_many_link_factory("aiod_entry", "person", table_prefix="editor"),
    )
    status_identifier: int | None = Field(foreign_key=Status.__tablename__ + ".identifier")
    status: Status | None = Relationship()

    # date_modified is updated in the resource_router
    date_modified: datetime | None = Field(default_factory=datetime.utcnow)
    date_created: datetime | None = Field(default_factory=datetime.utcnow)

    creator_identifier: str = Field(max_length=32 + 4, default="")

    class RelationshipConfig:
        editor: list[int] = ManyToMany()  # No deletion triggers: "orphan" Persons should be kept
        status: str | None = ManyToOne(
            example="draft",
            identifier_name="status_identifier",
            deserializer=FindByNameDeserializer(Status),
        )

    def owned_by(self, user: "User") -> bool:
        return self.creator_identifier == user.subject_identifier


class AIoDEntryCreate(AIoDEntryBase):
    editor: list[int] = Field(
        description="Links to identifiers of persons responsible for maintaining the entry.",
        default_factory=list,
        schema_extra={"example": []},
    )
    status: str | None = Field(
        description="Status of the entry (published, draft, rejected)",
        schema_extra={"example": "published"},
        default="draft",
    )


class AIoDEntryRead(AIoDEntryBase):
    editor: list[int] = Field(
        description="Links to identifiers of persons responsible for maintaining the entry.",
        default_factory=list,
        schema_extra={"example": []},
    )
    status: str | None = Field(
        description="Status of the entry (published, draft, rejected)",
        schema_extra={"example": "published"},
        default="draft",
    )
    date_modified: datetime | None = Field(
        description="The datetime on which the metadata was last updated in the AIoD platform,"
        "in UTC.  Note the difference between `.aiod_entry.date_created` and `.date_published`: "
        "the former is automatically set to the datetime the resource was created on AIoD, while "
        "the latter can optionally be set to an earlier datetime that the resource was published "
        "on an external platform.",
        schema_extra={"example": "2023-01-01T15:15:00.000"},
    )
    date_created: datetime | None = Field(
        description="The datetime on which the metadata was first published on the AIoD platform, "
        "in UTC.",
        schema_extra={"example": "2022-01-01T15:15:00.000"},
    )

    class Config:
        getter_dict = create_getter_dict(
            {"editor": AttributeSerializer("identifier"), "status": AttributeSerializer("name")}
        )
