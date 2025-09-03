from datetime import datetime
from typing import Optional, cast

from pydantic import condecimal
from sqlmodel import Field, Relationship, SQLModel

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
from database.model.resource_read_and_create import resource_read, resource_create, resource_update
from versioning import Version, VersionedResource, VersionedResourceCollection, schema_transform


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


def project_v3_to_v2() -> VersionedResource:
    """Name change: total_cost_euro -> total_cost_euros"""
    old_parameter = dict(
        total_cost_euro=(
            condecimal(max_digits=12, decimal_places=2) | None,
            Field(  # type: ignore
                description="The total budget of the project in euros.",
                schema_extra={"example": 1000000},
                default=None,
            ),
        ),
    )
    mapping = dict(total_cost_euros="total_cost_euro")

    ProjectV2Read = schema_transform(
        resource_read(Project),
        "ProjectV2Read",
        add_fields=old_parameter,
    )
    ProjectV2Update = schema_transform(
        resource_update(Project),
        "ProjectV2Update",
        add_fields=old_parameter,
    )
    ProjectV2Create = schema_transform(
        resource_create(Project),
        "ProjectV2Create",
        add_fields=old_parameter,
    )

    def orm_to_read(project: Project) -> ProjectV2Read:  # type: ignore[valid-type]
        read = resource_read(Project).model_validate(project).model_dump()
        for new_name, old_name in mapping.items():
            read[old_name] = getattr(project, new_name)
        return ProjectV2Read.model_validate(read)

    def update_data(data: dict) -> dict:
        new_data = data.copy()
        # v2 -> v3, in this case only renaming is necessary
        for new_name, old_name in mapping.items():
            old = data.get(old_name)
            new = data.get(new_name)

            if (old and new) and old != new:
                raise ValueError(
                    f"'{old_name}' and '{new_name}' are both specified, but with different values. Please only use one or the other."
                )

            new_data[new_name] = new or old
            new_data.pop(old_name, None)
        return new_data

    def create_to_orm(project: ProjectV2Create) -> Project:  # type: ignore[valid-type]
        fields = cast(SQLModel, project).model_dump()
        fields = update_data(fields)
        return Project.model_validate(fields)

    return VersionedResource(
        Project,
        ProjectV2Create,
        ProjectV2Update,
        ProjectV2Read,
        create_to_orm,
        update_data,
        orm_to_read,
    )


project_versions = VersionedResourceCollection(
    {
        Version.V3: VersionedResource(Project),
        Version.V2: project_v3_to_v2(),
        Version.LATEST: VersionedResource(Project),
    }
)
