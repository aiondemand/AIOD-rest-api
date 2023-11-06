from typing import Optional

from sqlmodel import Field, Relationship

from database.model.ai_resource.resource import AIResource, AIResourceBase
from database.model.educational_resource.educational_resource_type import EducationalResourceType
from database.model.field_length import NORMAL
from database.model.relationships import ManyToOne
from database.model.serializers import AttributeSerializer, FindByNameDeserializer


class EducationalResourceBase(AIResourceBase):
    level: str | None = Field(
        description="The educational level of this resource, for instance "
        "using the European Qualifications Framework.",
        max_length=NORMAL,
        schema_extra={"example": "EQF Level 3"},
    )


class EducationalResource(
    EducationalResourceBase, AIResource, table=True
):  # type: ignore [call-arg]
    __tablename__ = "educational_resource"

    type_identifier: int | None = Field(
        foreign_key=EducationalResourceType.__tablename__ + ".identifier"
    )
    type: Optional[EducationalResourceType] = Relationship()

    class RelationshipConfig(AIResource.RelationshipConfig):
        type: Optional[str] = ManyToOne(
            description="The type of educational resource.",
            identifier_name="type_identifier",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(EducationalResourceType),
            example="presentation",
        )
