from typing import Optional

from sqlmodel import Field, Relationship

from database.model.agent.agent_table import AgentTable
from database.model.ai_asset.ai_asset import AIAssetBase, AIAsset
from database.model.ai_resource.location import LocationORM, Location
from database.model.dataset.size import Size, SizeORM
from database.model.field_length import NORMAL, SHORT
from database.model.helper_functions import link_factory
from database.model.relationships import ResourceRelationshipList, ResourceRelationshipSingle
from database.model.serializers import (
    AttributeSerializer,
    FindByIdentifierDeserializer,
    CastDeserializer,
)


class DatasetBase(AIAssetBase):
    issn: str | None = Field(
        description="The International Standard Serial Number, ISSN, an identifier for serial "
        "publications.",
        min_length=8,
        max_length=8,
        default=None,
        schema_extra={"example": "20493630"},
    )
    measurement_technique: str | None = Field(
        description="The technique, technology, or methodology used in a dataset, corresponding to "
        "the method used for measuring the corresponding variable(s).",
        max_length=NORMAL,
        schema_extra={"example": "mass spectrometry"},
        default=None,
    )
    temporal_coverage: str | None = Field(
        description="The temporalCoverage of a CreativeWork indicates the period that the content "
        "applies to, i.e. that it describes, a textual string indicating a time period "
        "in ISO 8601 time interval format. In the case of a Dataset it will typically "
        "indicate the relevant time period in a precise notation (e.g. for a 2011 "
        "census dataset, the year 2011 would be written '2011/2012').",
        max_length=SHORT,
        schema_extra={"example": "2011/2012"},
        default=None,
    )


class Dataset(DatasetBase, AIAsset, table=True):  # type: ignore [call-arg]
    __tablename__ = "dataset"

    funder: list["AgentTable"] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"},
        link_model=link_factory("dataset", AgentTable.__tablename__, table_prefix="funder"),
    )
    size_identifier: int | None = Field(foreign_key=SizeORM.__tablename__ + ".identifier")
    size: Optional[SizeORM] = Relationship()
    spatial_coverage_identifier: int | None = Field(
        foreign_key=LocationORM.__tablename__ + ".identifier"
    )
    spatial_coverage: Optional[LocationORM] = Relationship()

    class RelationshipConfig(AIAsset.RelationshipConfig):
        funder: list[int] = ResourceRelationshipList(
            description="Links to identifiers of the agents (person or organization) that supports "
            "this dataset through some kind of financial contribution. ",
            serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializer(AgentTable),
            default_factory_pydantic=list,
            example=[],
        )
        size: Optional[Size] = ResourceRelationshipSingle(
            description="The size of this dataset, for example the number of rows. The file size "
            "should not be included here, but in distribution.content_size_kb.",
            deserializer=CastDeserializer(SizeORM),
        )
        spatial_coverage: Optional[Location] = ResourceRelationshipSingle(
            description="A location that describes the spatial aspect of this dataset. For "
            "example, a point where all the measurements were collected.",
            deserializer=CastDeserializer(LocationORM),
        )
