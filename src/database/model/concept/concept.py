import copy
import datetime
import os
from typing import Optional, Tuple, TYPE_CHECKING

from pydantic import validator
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql.functions import coalesce
from sqlmodel import SQLModel, Field, Relationship

from database.model.concept.aiod_entry import AIoDEntryORM, AIoDEntryRead, AIoDEntryCreate
from database.model.field_length import SHORT, NORMAL
from database.model.platform.platform_names import PlatformName
from database.model.relationships import OneToOne
from database.model.serializers import CastDeserializer
from database.validators import huggingface_validators, openml_validators, zenodo_validators

if TYPE_CHECKING:
    from authentication import User

IS_SQLITE = os.getenv("DB") == "SQLite"
CONSTRAINT_LOWERCASE = f"{'platform' if IS_SQLITE else 'BINARY(platform)'} = LOWER(platform)"


class AIoDConceptBase(SQLModel):
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
        "'platform'. Leave empty if this item is not part of an external platform. For example, "
        "for HuggingFace, this should be the <namespace>/<dataset_name>, and for Openml, the "
        "OpenML identifier.",
        default=None,
        schema_extra={"example": "1"},
    )

    @validator("platform_resource_identifier")
    def platform_resource_identifier_valid(cls, platform_resource_identifier: str, values) -> str:
        """
        Throw a ValueError if the platform_resource_identifier is invalid for this platform.

        Note that field order matters: platform is defined before platform_resource_identifier,
        so that this validator can use the value of the platform. Refer to
        https://docs.pydantic.dev/1.10/usage/models/#field-ordering
        """
        if platform := values.get("platform", None):
            match platform:
                case PlatformName.huggingface:
                    huggingface_validators.throw_error_on_invalid_identifier(
                        platform_resource_identifier
                    )
                case PlatformName.openml:
                    openml_validators.throw_error_on_invalid_identifier(
                        platform_resource_identifier
                    )
                case PlatformName.zenodo:
                    zenodo_validators.throw_error_on_invalid_identifier(
                        platform_resource_identifier
                    )
        return platform_resource_identifier


class AIoDConcept(AIoDConceptBase):
    identifier: int = Field(default=None, primary_key=True)
    date_deleted: datetime.datetime | None = Field()
    aiod_entry_identifier: int | None = Field(
        foreign_key=AIoDEntryORM.__tablename__ + ".identifier",
        unique=True,
    )
    aiod_entry: AIoDEntryORM = Relationship()

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

    @classmethod
    def table_arguments(cls) -> list:
        """This function can be implemented by children of this class, to add additional table
        arguments"""
        return []

    @declared_attr
    def __table_args__(cls) -> Tuple:
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
        ) + tuple(cls.table_arguments())

    def owned_by(self, user: "User") -> bool:
        assert self.aiod_entry is not None, f"Expected concept to have aiod_entry: {self}"
        return self.aiod_entry.owned_by(user)
