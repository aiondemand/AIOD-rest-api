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
from database.model.resource_read_and_create import resource_read, resource_create
from versioning import Version, VersionedResource, schema_transform, VersionedResourceCollection


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
    total_cost_euros: condecimal(max_digits=12, decimal_places=2) | None = Field(  # type: ignore
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


old_parameter = dict(
    total_cost_euro=(
        condecimal(max_digits=12, decimal_places=2) | None,
        Field(
            description="The total budget of the project in euros.",
            schema_extra={"example": 1000000},
            default=None,
        ),
    )
)
ProjectV2Read = schema_transform(
    resource_read(Project), name="ProjectV2Read", add_fields=old_parameter
)
ProjectV2Create = schema_transform(
    resource_create(Project),
    name="ProjectV2Create",
    add_fields=old_parameter,
)


def rename_total_cost_euro(create: ProjectV2Create) -> Project:  # type: ignore[valid-type]
    fields = create.model_dump()  # type: ignore[attr-defined]
    old_value = fields.get("total_cost_euro")
    new_value = fields.get("total_cost_euros")
    if (old_value and new_value) and (old_value != new_value):
        raise ValueError(
            "Both `total_cost_euro` and `total_cost_euros` are defined with different values."
        )
    fields["total_cost_euros"] = old_value or new_value
    return Project.model_validate(fields)


def add_total_cost_euro(project: Project) -> ProjectV2Read:  # type: ignore[valid-type]
    fields = resource_read(Project).model_validate(project).model_dump()
    fields["total_cost_euro"] = project.total_cost_euros
    return ProjectV2Read.model_validate(fields)


project_versions = VersionedResourceCollection(
    {
        Version.V3: VersionedResource(Project),
        Version.V2: VersionedResource[Project](
            Project,
            ProjectV2Create,
            ProjectV2Read,
            create_to_orm=rename_total_cost_euro,
            orm_to_read=add_total_cost_euro,
        ),
        Version.LATEST: VersionedResource(Project),
    }
)
