from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database.model.ai_resource import OrmAIResource


class OrmCodeArtifact(OrmAIResource):
    """Any publication."""

    __tablename__ = "codeArtifacts"
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    doi: Mapped[str] = mapped_column(String(150), nullable=True)
