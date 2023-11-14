import copy
import datetime
import os
from typing import Optional, Tuple

from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql.functions import coalesce
from sqlmodel import SQLModel, Field, Relationship

from database.model.concept.aiod_entry import AIoDEntryORM, AIoDEntryRead, AIoDEntryCreate
from database.model.field_length import SHORT, NORMAL
from database.model.platform.platform_names import PlatformName
from database.model.relationships import OneToOne
from database.model.serializers import CastDeserializer

IS_SQLITE = os.getenv("DB") == "SQLite"
CONSTRAINT_LOWERCASE = f"{'platform' if IS_SQLITE else 'BINARY(platform)'} = LOWER(platform)"


class AIoDConceptBase(SQLModel):
    """The AIoDConcept is the top-level (abstract) class in AIoD."""

    platform: str | None = Field(
        max_length=SHORT,
        default=None,
        description="The external platform from which this resource originates. Leave empty if "
        "this item originates from AIoD. If platform is not None, the "
        "platform_resource_identifier should be set as well.",
        schema_extra={"example": PlatformName.example},
        foreign_key="platform.name",
    )
    platform_resource_identifier: str | None = Field(
        max_length=NORMAL,
        description="A unique identifier issued by the external platform that's specified in "
        "'platform'. Leave empty if this item is not part of an external platform.",
        default=None,
        schema_extra={"example": "1"},
    )


class AIoDConcept(AIoDConceptBase):
    identifier: int = Field(default=None, primary_key=True)
    date_deleted: datetime.datetime | None = Field()
    aiod_entry_identifier: int | None = Field(
        foreign_key=AIoDEntryORM.__tablename__ + ".identifier",
        unique=True,
    )
    aiod_entry: AIoDEntryORM = Relationship()

    # body_identifier: int | None = Field(foreign_key=Body.__tablename__ + ".identifier")
    # body: Body | None = Relationship()

    def __init_subclass__(cls):
        """Fixing problems with the inheritance of relationships."""
        cls.__annotations__.update(AIoDConcept.__annotations__)
        relationships = copy.deepcopy(AIoDConcept.__sqlmodel_relationships__)
        cls.__sqlmodel_relationships__.update(relationships)

    class RelationshipConfig:
        aiod_entry: Optional[AIoDEntryRead] = OneToOne(
            deserializer=CastDeserializer(AIoDEntryORM),
            default_factory_pydantic=AIoDEntryCreate,
            class_read=Optional[AIoDEntryRead],
            class_create=Optional[AIoDEntryCreate],
            on_delete_trigger_deletion_by="aiod_entry_identifier",
        )
        # body: Optional[Body] = ResourceRelationshipSingle(
        #     deserializer=CastDeserializer(Body),
        # )

    @declared_attr
    def __table_args__(cls) -> Tuple:
        # Note to developer: this will give problems if we'll add another child which has extra
        # constraints, because this might lead to a duplicate check constraint name.
        # TODO: solve it when this becomes a problem.
        return (
            Index(
                f"{cls.__name__}_same_platform_and_platform_id",
                cls.platform,
                cls.platform_resource_identifier,
                coalesce(cls.date_deleted, "2000-01-01"),
                unique=True,
            ),
            CheckConstraint(
                "(platform IS NULL) <> (platform_resource_identifier IS NOT NULL)",
                name=f"{cls.__name__}_platform_xnor_platform_id_null",
            ),
            CheckConstraint(CONSTRAINT_LOWERCASE, name=f"{cls.__name__}_platform_lowercase"),
        )
