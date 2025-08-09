import copy
import datetime
import os
from typing import Optional, Tuple, Any, Callable

from pydantic import validator
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql.functions import coalesce
from sqlmodel import SQLModel, Field, Relationship

from database.model.concept.aiod_entry import AIoDEntryORM, AIoDEntryRead, AIoDEntryCreate
from database.model.field_length import SHORT, NORMAL, IDENTIFIER_LENGTH
from database.model.platform.platform_names import PlatformName
from database.model.relationships import OneToOne
from database.model.serializers import CastDeserializer
from database.validators import huggingface_validators, openml_validators, zenodo_validators
from database.identifiers import create_id_generator

IS_SQLITE = os.getenv("DB") == "SQLite"
CONSTRAINT_LOWERCASE = f"{'platform' if IS_SQLITE else 'BINARY(platform)'} = LOWER(platform)"


class AIoDConceptBase(SQLModel):
    platform: str | None = Field(
        max_length=SHORT,
        default=None,
        schema_extra=dict(examples=[None, "aiod", "huggingface", "zenodo"]),
        description="The platform from which this resource originates. "
        "Defaults to `aiod` for assets registered directly on AI-on-Demand. "
        "This field should only be set by connectors, "
        "leave empty for users submitting assets. "
        "If platform is not None, `platform_resource_identifier` should also be set.",
        foreign_key="platform.name",
    )

    platform_resource_identifier: str | None = Field(
        max_length=NORMAL,
        default=None,
        schema_extra=dict(
            examples=[
                None,
                "data_rPQvKrL8cgXhtL4HEHijXSiC",
                "621ffdd236468d709f181d58",
                "zenodo.org:10000008",
            ]
        ),
        description="The identifier by which the external platform (from `platform`) identifies the asset. "
        "Defaults to the asset identifier for assets registered directly on AIoD. "
        "This field should only be set by connectors, "
        "leave empty for users submitting assets. ",
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
    identifier: str = Field(
        max_length=IDENTIFIER_LENGTH,
        default=None,
        primary_key=True,
    )
    date_deleted: datetime.datetime | None = Field()
    aiod_entry_identifier: int | None = Field(
        foreign_key=AIoDEntryORM.__tablename__ + ".identifier",
        unique=True,
    )

    aiod_entry: AIoDEntryORM = Relationship()

    _id_generator: Callable[[], str] | None = None

    @validator("identifier", pre=True, always=True)
    def set_dynamic_default_identifier(cls, v) -> str:
        if isinstance(v, str):
            return v
        if not cls._id_generator:
            # TODO: Centralize validation probably, so we can check against duplicate abbreviations
            abbreviation = getattr(cls, "__abbreviation__", None)
            if abbreviation is None:
                raise ValueError(
                    f"{cls}.__abbreviation__ not set. Must be a string of at most 4 characters."
                )
            if not isinstance(abbreviation, str) or len(abbreviation) > 4:
                raise ValueError(
                    f"{cls}.__abbreviation__ must be a string of at most 4 characters, is {abbreviation!r}"
                )
            cls._id_generator = create_id_generator(prefix=abbreviation)
        return cls._id_generator()

    def __init_subclass__(cls):
        """Fixing problems with the inheritance of relationships."""
        cls.__annotations__.update(AIoDConcept.__annotations__)
        relationships = copy.deepcopy(AIoDConcept.__sqlmodel_relationships__)
        cls.__sqlmodel_relationships__.update(relationships)

    class RelationshipConfig:
        aiod_entry: Optional[AIoDEntryRead] = OneToOne(
            deserializer=CastDeserializer(AIoDEntryORM),
            default_factory_pydantic=AIoDEntryCreate,
            default_factory_orm=AIoDEntryORM,
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
