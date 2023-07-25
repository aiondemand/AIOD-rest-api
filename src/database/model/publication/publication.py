from datetime import datetime
from typing import Optional, List
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from database.model.dataset.publication_link import DatasetPublicationLink
from database.model.general.license import License
from database.model.general.resource_type import ResourceType
from database.model.relationships import ResourceRelationshipList, ResourceRelationshipSingle
from serialization import (
    AttributeSerializer,
    FindByNameDeserializer,
)

if TYPE_CHECKING:
    from database.model.dataset.dataset import Dataset

from database.model.ai_asset_old import AIAssetOld


class PublicationBase(AIAssetOld):
    # Required fields
    title: str = Field(max_length=250, schema_extra={"example": "A publication"})

    # Recommended fields
    doi: str | None = Field(max_length=150, schema_extra={"example": "0000000/000000000000"})
    creators: str | None = Field(max_length=450, schema_extra={"example": "John Doe"})
    access_right: str | None = Field(max_length=150, schema_extra={"example": "open access"})
    date_created: datetime | None = Field(
        default=None, schema_extra={"example": "2022-01-01T15:15:00.000Z"}
    )
    date_published: datetime | None = Field(
        default=None, schema_extra={"example": "2023-01-01T15:15:00.000Z"}
    )
    url: str | None = Field(
        max_length=250, schema_extra={"example": "https://www.example.com/publication/example"}
    )


class Publication(PublicationBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "publication"

    identifier: int = Field(primary_key=True, foreign_key="ai_asset.identifier")

    license_identifier: int | None = Field(foreign_key="license.identifier")
    license: Optional[License] = Relationship(back_populates="publications")

    datasets: List["Dataset"] = Relationship(
        back_populates="citations", link_model=DatasetPublicationLink
    )
    resource_type_identifier: int | None = Field(foreign_key="resource_type.identifier")
    resource_type: Optional[ResourceType] = Relationship(back_populates="publications")

    class RelationshipConfig:
        datasets: List[int] = ResourceRelationshipList(
            serializer=AttributeSerializer("identifier"), example=[1]
        )
        license: Optional[str] = ResourceRelationshipSingle(
            identifier_name="license_identifier",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(License),
            example="https://creativecommons.org/share-your-work/public-domain/cc0/",
        )
        resource_type: Optional[str] = ResourceRelationshipSingle(
            identifier_name="resource_type_identifier",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ResourceType),
            example="journal article",
        )
