from database.model.resource import OrmResource
from sqlalchemy import UniqueConstraint


class OrmAIResource(OrmResource):
    """The base class of all our AIResources such as Datasets, Publications etc..
    For now, it contains no fields, we will have to extend it later."""

    __tablename__ = "ai_resources"
    __table_args__ = (
        UniqueConstraint(
            "platform",
            "platform_identifier",
            name="ai_resource_unique_platform_platform_identifier",
        ),
    )

    __mapper_args__ = {"polymorphic_identity": "ai_resource", "with_polymorphic": "*"}
