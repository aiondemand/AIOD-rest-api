from typing import Optional

from sqlmodel import Field, Relationship

from database.model.ai_resource.resource import AIResource, AIResourceBase
from database.model.ai_resource.text import TextORM, Text
from database.model.field_length import NORMAL, LONG
from database.model.helper_functions import many_to_many_link_factory
from database.model.news.news_category import NewsCategory
from database.model.relationships import ManyToMany, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    CastDeserializer,
    FindByNameDeserializerList,
)
from versioning import Version, VersionedResource, VersionedResourceCollection


class NewsBase(AIResourceBase):
    headline: str | None = Field(
        description="A short headline given to this news item.",
        max_length=NORMAL,
        schema_extra={"example": "A headline to show on top of the page."},
    )
    alternative_headline: str | None = Field(
        description="An alternative headline given to this news item.",
        max_length=NORMAL,
        schema_extra={"example": "An alternative headline."},
    )
    source: str | None = Field(
        description="Location where the news item was originally published.",
        max_length=LONG,
        schema_extra={
            "example": "https://tailor-network.eu/shaping-the-future-of-ai-within-the-eu/"
        },
    )


class News(NewsBase, AIResource, table=True):  # type: ignore [call-arg]
    __tablename__ = "news"
    __abbreviation__ = "news"
    __plural__ = "news"

    category: list[NewsCategory] = Relationship(  # type: ignore[valid-type]
        link_model=many_to_many_link_factory(
            "news", NewsCategory.__tablename__, from_identifier_type=str
        )
    )
    content_identifier: int | None = Field(
        index=True,
        description="Alternative for using .distributions[*].content_url, to make it easier to add "
        "textual content. ",
        foreign_key="text.identifier",
    )
    content: TextORM | None = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[News.content_identifier]")
    )

    class RelationshipConfig(AIResource.RelationshipConfig):
        category: list[str] = ManyToMany(
            description="News categories related to this item.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(NewsCategory),
            example=["Education"],
            default_factory_pydantic=list,
        )
        content: Optional[Text] = OneToOne(
            deserializer=CastDeserializer(TextORM),
            on_delete_trigger_deletion_by="content_identifier",
        )


news_versions = VersionedResourceCollection(
    {
        Version.V2: VersionedResource(News),
        Version.LATEST: VersionedResource(News),
    }
)
