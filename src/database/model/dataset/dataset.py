from datetime import datetime
from typing import Optional, List

from sqlalchemy import UniqueConstraint, Column, Integer, ForeignKey
from sqlmodel import Field, Relationship, SQLModel

from database.model.ai_asset_old import AIAssetOld
from database.model.dataset.alternate_name import DatasetAlternateNameLink, DatasetAlternateName
from database.model.dataset.data_download import DataDownloadORM, DataDownload
from database.model.dataset.keyword_link import DatasetKeywordLink
from database.model.dataset.measured_value import (
    DatasetMeasuredValueNameLink,
    MeasuredValueORM,
    MeasuredValue,
)
from database.model.dataset.publication_link import DatasetPublicationLink
from database.model.general.keyword import Keyword
from database.model.general.license import License
from database.model.publication.publication import Publication
from database.model.relationships import ResourceRelationshipList, ResourceRelationshipSingle
from database.model.resource import Resource
from serialization import (
    AttributeSerializer,
    FindByNameDeserializer,
    CastDeserializer,
    FindByIdentifierDeserializer,
)


class DatasetParentChildLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "dataset_parent_child_link"
    parent_identifier: int = Field(
        sa_column=Column(
            Integer, ForeignKey("dataset.identifier", ondelete="CASCADE"), primary_key=True
        )
    )
    child_identifier: int = Field(
        sa_column=Column(
            Integer, ForeignKey("dataset.identifier", ondelete="CASCADE"), primary_key=True
        )
    )


class DatasetBase(AIAssetOld):
    # Required fields
    description: str = Field(max_length=5000, schema_extra={"example": "A description."})
    name: str = Field(max_length=150, schema_extra={"example": "Example Dataset"})
    same_as: str = Field(
        max_length=150,
        unique=True,
        schema_extra={"example": "https://www.example.com/dataset/example"},
    )

    # Recommended fields
    contact: str | None = Field(max_length=150, default=None, schema_extra={"example": "John Doe"})
    creator: str | None = Field(max_length=150, default=None, schema_extra={"example": "John Doe"})
    publisher: str | None = Field(
        max_length=150, default=None, schema_extra={"example": "John Doe"}
    )
    # TODO(issue 9): contact + creator + publisher repeated organization/person
    date_modified: datetime | None = Field(
        default=None, schema_extra={"example": "2023-01-01T15:15:00.000Z"}
    )
    date_published: datetime | None = Field(
        default=None, schema_extra={"example": "2022-01-01T15:15:00.000Z"}
    )
    funder: str | None = Field(max_length=150, default=None, schema_extra={"example": "John Doe"})
    # TODO(issue 9): funder repeated organization/person
    is_accessible_for_free: bool = Field(default=True)
    issn: str | None = Field(max_length=8, default=None, schema_extra={"example": "12345679"})
    size: int | None = Field(schema_extra={"example": 100})
    spatial_coverage: str | None = Field(
        max_length=500, default=None, schema_extra={"example": "New York"}
    )
    temporal_coverage_from: datetime | None = Field(
        default=None, schema_extra={"example": "2020-01-01T00:00:00.000Z"}
    )
    temporal_coverage_to: datetime | None = Field(
        default=None, schema_extra={"example": "2021-01-01T00:00:00.000Z"}
    )
    version: str | None = Field(max_length=150, default=None, schema_extra={"example": "1.1.0"})


class Dataset(DatasetBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "dataset"

    __table_args__ = Resource.__table_args__ + (
        UniqueConstraint(
            "name",
            "version",
            name="same_name_and_version",
        ),
    )

    identifier: int = Field(primary_key=True, foreign_key="ai_asset.identifier")

    license_identifier: int | None = Field(foreign_key="license.identifier")
    license: Optional[License] = Relationship(back_populates="datasets")
    alternate_names: List[DatasetAlternateName] = Relationship(
        back_populates="datasets", link_model=DatasetAlternateNameLink
    )
    citations: List[Publication] = Relationship(
        back_populates="datasets",
        link_model=DatasetPublicationLink,
    )
    distributions: List[DataDownloadORM] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"}
    )
    has_parts: List["Dataset"] = Relationship(
        back_populates="is_part",
        link_model=DatasetParentChildLink,
        sa_relationship_kwargs=dict(
            primaryjoin="Dataset.identifier==DatasetParentChildLink.parent_identifier",
            secondaryjoin="Dataset.identifier==DatasetParentChildLink.child_identifier",
            cascade="all, delete",
        ),
    )
    is_part: List["Dataset"] = Relationship(
        back_populates="has_parts",
        link_model=DatasetParentChildLink,
        sa_relationship_kwargs=dict(
            primaryjoin="Dataset.identifier==DatasetParentChildLink.child_identifier",
            secondaryjoin="Dataset.identifier==DatasetParentChildLink.parent_identifier",
            cascade="all, delete",
        ),
    )
    keywords: List[Keyword] = Relationship(back_populates="datasets", link_model=DatasetKeywordLink)
    measured_values: List[MeasuredValueORM] = Relationship(
        back_populates="datasets", link_model=DatasetMeasuredValueNameLink
    )

    class RelationshipConfig:
        alternate_names: List[str] = ResourceRelationshipList(
            example=["alias 1", "alias 2"],
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(DatasetAlternateName),
        )
        citations: List[int] = ResourceRelationshipList(
            example=[],
            deserializer=FindByIdentifierDeserializer(Publication),
            serializer=AttributeSerializer("identifier"),
        )
        distributions: List[DataDownload] = ResourceRelationshipList(
            deserializer=CastDeserializer(DataDownloadORM)
        )
        is_part: List[int] = ResourceRelationshipList(
            example=[],
            serializer=AttributeSerializer("identifier"),
        )
        has_parts: List[int] = ResourceRelationshipList(
            example=[],
            serializer=AttributeSerializer("identifier"),
        )
        license: Optional[str] = ResourceRelationshipSingle(
            identifier_name="license_identifier",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(License),
            example="https://creativecommons.org/share-your-work/public-domain/cc0/",
        )
        keywords: List[str] = ResourceRelationshipList(
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Keyword),
            example=["keyword1", "keyword2"],
        )
        measured_values: List[MeasuredValue] = ResourceRelationshipList(
            deserializer=CastDeserializer(MeasuredValueORM)
        )


# Defined separate because it references Dataset, and can therefor not be defined inside Dataset
deserializer = FindByIdentifierDeserializer(Dataset)
Dataset.RelationshipConfig.is_part.deserializer = deserializer  # type: ignore[attr-defined]
Dataset.RelationshipConfig.has_parts.deserializer = deserializer  # type: ignore[attr-defined]
Publication.RelationshipConfig.datasets.deserializer = deserializer  # type: ignore[attr-defined]
