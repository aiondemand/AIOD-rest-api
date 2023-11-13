from typing import Optional

from sqlmodel import Field, Relationship

from database.model.ai_asset.ai_asset import AIAssetBase, AIAsset
from database.model.computational_asset.computational_asset_type import ComputationalAssetType
from database.model.field_length import NORMAL
from database.model.relationships import ManyToOne
from database.model.serializers import AttributeSerializer, FindByNameDeserializer


class ComputationalAssetBase(AIAssetBase):
    status_info: str | None = Field(
        description="A webpage that shows the current status of this asset.",
        max_length=NORMAL,
        schema_extra={"example": "https://www.example.com/cluster-status"},
    )


class ComputationalAsset(ComputationalAssetBase, AIAsset, table=True):  # type: ignore [call-arg]
    """
    An asset providing access to computational resources for processing or storage.

    Currently, the ComputationalAsset doesn't contain many fields. We will probably use a
    separate, dedicated database to store the computational assets, in which case the AIoD
    Metadata Catalogue will not contain many field, just a link to the record in the dedicated
    database.
    """

    __tablename__ = "computational_asset"

    type_identifier: int | None = Field(
        foreign_key=ComputationalAssetType.__tablename__ + ".identifier"
    )
    type: Optional[ComputationalAssetType] = Relationship()

    class RelationshipConfig(AIAsset.RelationshipConfig):
        type: Optional[str] = ManyToOne(
            description="The type of computational asset.",
            identifier_name="type_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ComputationalAssetType),
            example="storage",
        )
