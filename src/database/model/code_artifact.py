from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.model.ai_resource import OrmAIResource


class OrmCodeArtifact(OrmAIResource):
    """Any publication."""

    __tablename__ = "code_artifacts"
    __table_args__ = (
        UniqueConstraint(
            "platform",
            "platform_identifier",
            name="publication_unique_platform_platform_identifier",
        ),
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    doi: Mapped[str] = mapped_column(String(150), nullable=True)
