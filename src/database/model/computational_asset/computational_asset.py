from sqlmodel import Field, Relationship
from typing import Optional
from database.model.field_length import NORMAL
from database.model.relationships import ManyToOne, OneToMany
from database.model.serializers import (
    AttributeSerializer,
    CastDeserializerList,
    FindByNameDeserializer,
)

from database.model.ai_asset.ai_asset import AIAssetBase, AIAsset
from database.model.computational_asset.computational_asset_type import ComputationalAssetType

from database.model.computational_asset.cpu import Cpu, CpuORM
from database.model.computational_asset.memory import Memory, MemoryORM
from database.model.computational_asset.accelerator import Accelerator, AcceleratorORM
from database.model.computational_asset.storage import Storage, StorageORM


class ComputationalAssetBase(AIAssetBase):
    status_info: str | None = Field(
        description="A webpage that shows the current status of this asset.",
        max_length=NORMAL,
        schema_extra={"example": "https://www.example.com/cluster-status"},
    )
    os: str | None = Field(
        description="The operating system installed in the Computational Asset.",
        max_length=NORMAL,
        schema_extra={"example": "Redhat"},
    )
    kernel: str | None = Field(
        description="TBC",
        max_length=NORMAL,
        schema_extra={"example": "Linux"},
    )
    pricing_scheme: str | None = Field(
        description="",
        schema_extra={"example": ""},
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
    cpu: list[CpuORM] = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    memory: list[MemoryORM] = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    accelerator: list[AcceleratorORM] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"}
    )
    storage: list[StorageORM] = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})

    class RelationshipConfig(AIAsset.RelationshipConfig):
        type: Optional[str] = ManyToOne(
            description="The type of computational asset.",
            identifier_name="type_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ComputationalAssetType),
            example="storage",
        )

        cpu: list[Cpu] | None = OneToMany(
            default_factory_pydantic=list,  # no deletion trigger: cascading delete is used
            description="The CPU of the Computational Asset.",
            deserializer=CastDeserializerList(CpuORM),
            example=[],
        )

        memory: list[Memory] | None = OneToMany(
            default_factory_pydantic=list,  # no deletion trigger: cascading delete is used
            description="The Memory of Computational Asset.",
            deserializer=CastDeserializerList(MemoryORM),
            example=[],
        )
        accelerator: list[Accelerator] | None = OneToMany(
            default_factory_pydantic=list,  # no deletion trigger: cascading delete is used
            description="The Accelerator integrated into the Computational Asset.",
            deserializer=CastDeserializerList(AcceleratorORM),
            example=[],
        )
        storage: list[Storage] | None = OneToMany(
            default_factory_pydantic=list,  # no deletion trigger: cascading delete is used
            description="The Storage associated with the Computational Asset.",
            deserializer=CastDeserializerList(StorageORM),
            example=[],
        )
