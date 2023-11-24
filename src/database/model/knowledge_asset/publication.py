from typing import Optional

from sqlmodel import Field, Relationship

from database.model.ai_asset.ai_asset import AIAsset
from database.model.ai_resource.text import Text, TextORM
from database.model.field_length import NORMAL
from database.model.knowledge_asset.PublicationType import PublicationType
from database.model.knowledge_asset.knowledge_asset import KnowledgeAssetBase, KnowledgeAsset
from database.model.relationships import ManyToOne, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    FindByNameDeserializer,
    CastDeserializer,
    FindByIdentifierDeserializerList,
)


class PublicationBase(KnowledgeAssetBase):
    permanent_identifier: str | None = Field(
        description="A Permanent Identifier (e.g. DOI) for the entity",
        max_length=NORMAL,
        schema_extra={"example": "http://dx.doi.org/10.1093/ajae/aaq063"},
        default=None,
    )
    isbn: str | None = Field(
        description="The International Standard Book Number, ISBN, used to identify published "
        "books or, more rarely, journal issues.",
        min_length=10,
        max_length=13,
        default=None,
        schema_extra={"example": "9783161484100"},
    )
    issn: str | None = Field(
        description="The International Standard Serial Number, ISSN, an identifier for serial "
        "publications.",
        min_length=8,
        max_length=8,
        default=None,
        schema_extra={"example": "20493630"},
    )


class Publication(PublicationBase, KnowledgeAsset, table=True):  # type: ignore [call-arg]
    __tablename__ = "publication"

    content_identifier: int | None = Field(
        index=True,
        foreign_key="text.identifier",
        description="Alternative for using .distributions[*].content_url, to make it easier to add "
        "textual content. ",
    )
    content: TextORM | None = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[Publication.content_identifier]")
    )
    type_identifier: int | None = Field(foreign_key=PublicationType.__tablename__ + ".identifier")
    type: Optional[PublicationType] = Relationship()

    class RelationshipConfig(KnowledgeAsset.RelationshipConfig):
        content: Optional[Text] = OneToOne(
            deserializer=CastDeserializer(TextORM),
            on_delete_trigger_deletion_by="content_identifier",
        )
        type: str | None = ManyToOne(
            description="The type of publication.",
            identifier_name="type_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(PublicationType),
            example="journal",
        )


deserializer = FindByIdentifierDeserializerList(Publication)
AIAsset.RelationshipConfig.citation.deserializer = deserializer  # type: ignore
