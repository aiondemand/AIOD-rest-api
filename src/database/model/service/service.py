from sqlmodel import Field

from database.model.ai_resource.resource import AIResourceBase, AbstractAIResource
from database.model.field_length import NORMAL, LONG


class ServiceBase(AIResourceBase):
    slogan: str | None = Field(
        description="A slogan or motto associated with the service.",
        max_length=NORMAL,
        schema_extra={"example": "Making your Smart Paradigm Shifts more Disruptive"},
        default=None,
    )
    terms_of_service: str | None = Field(
        description="Human-readable terms of service documentation.",
        max_length=LONG,
        schema_extra={
            "example": "Your use of this service is subject to the following terms: [...]."
        },
        default=None,
    )


class Service(ServiceBase, AbstractAIResource, table=True):  # type: ignore [call-arg]
    __tablename__ = "service"

    class RelationshipConfig(AbstractAIResource.RelationshipConfig):
        pass
