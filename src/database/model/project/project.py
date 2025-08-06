from datetime import datetime
from typing import Optional

from pydantic import condecimal
from sqlmodel import Field, Relationship

from database.model.agent.organisation import Organisation
from database.model.ai_asset.ai_asset_table import AIAssetTable
from database.model.ai_resource.resource import AIResourceBase, AIResource
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToMany, ManyToOne
from database.model.serializers import (
    AttributeSerializer,
    FindByIdentifierDeserializerList,
)
from database.model.field_length import IDENTIFIER_LENGTH
from versioning import Version, VersionedResource, VersionedResourceCollection


class ProjectBase(AIResourceBase):
    start_date: datetime = Field(
        description="The start date and time of the project as ISO 8601.",
        default=None,
        schema_extra={"example": "2021-02-03T15:15:00"},
    )
    end_date: datetime | None = Field(
        description="The end date and time of the project as ISO 8601.",
        default=None,
        schema_extra={"example": "2022-01-01T15:15:00"},
    )
    total_cost_euro: condecimal(max_digits=12, decimal_places=2) | None = Field(  # type: ignore
        description="The total budget of the project in euros.",
        schema_extra={"example": 1000000},
        default=None,
    )


class Project(ProjectBase, AIResource, table=True):  # type: ignore [call-arg]
    __tablename__ = "project"
    __abbreviation__ = "proj"

    funder: list[Organisation] = Relationship(
        link_model=many_to_many_link_factory(
            "project",
            Organisation.__tablename__,
            table_prefix="funder",
            from_identifier_type=str,
            to_identifier_type=str,
        ),
    )
    participant: list[Organisation] = Relationship(
        link_model=many_to_many_link_factory(
            "project",
            Organisation.__tablename__,
            table_prefix="participant",
            from_identifier_type=str,
            to_identifier_type=str,
        ),
    )
    coordinator_identifier: str | None = Field(
        max_length=IDENTIFIER_LENGTH, foreign_key=Organisation.__tablename__ + ".identifier"
    )
    coordinator: Optional[Organisation] = Relationship()
    produced: list[AIAssetTable] = Relationship(
        link_model=many_to_many_link_factory(
            "project",
            AIAssetTable.__tablename__,
            table_prefix="produced",
            from_identifier_type=str,
            to_identifier_type=str,
        ),
    )
    used: list[AIAssetTable] = Relationship(
        link_model=many_to_many_link_factory(
            "project",
            AIAssetTable.__tablename__,
            table_prefix="used",
            from_identifier_type=str,
            to_identifier_type=str,
        ),
    )

    class RelationshipConfig(AIResource.RelationshipConfig):
        funder: list[str] = ManyToMany(
            description="Identifiers of organizations that support this project through some kind "
            "of financial contribution. ",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(Organisation),
            default_factory_pydantic=list,
            example=[],
        )
        participant: list[str] = ManyToMany(
            description="Identifiers of members of this project. ",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(Organisation),
            default_factory_pydantic=list,
            example=[],
        )
        coordinator: Optional[str] = ManyToOne(
            identifier_name="coordinator_identifier",
            description="The coordinating organisation of this project.",
            _serializer=AttributeSerializer("identifier"),
        )
        produced: list[str] = ManyToMany(
            description="Identifiers of AIAssets that are created in this project.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(AIAssetTable),
            default_factory_pydantic=list,
            example=[],
        )
        used: list[str] = ManyToMany(
            description="Identifiers of AIAssets that are used (but not created) in this project.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(AIAssetTable),
            default_factory_pydantic=list,
            example=[],
        )


project_versions = VersionedResourceCollection(
    {
        Version.V2: VersionedResource(Project),
        Version.LATEST: VersionedResource(Project),
    }
)
