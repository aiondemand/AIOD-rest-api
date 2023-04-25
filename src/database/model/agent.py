from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database.model.resource import OrmResource

from database.model.base import Base
from database.model.unique_model import UniqueMixin


class OrmEmail(UniqueMixin, Base):
    __tablename__ = "emails"

    @classmethod
    def _unique_hash(cls, email):
        return email

    @classmethod
    def _unique_filter(cls, query, email):
        return query.filter(cls.email == email)

    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)

    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("organisations.identifier", ondelete="cascade"), nullable=True, default=None
    )


class OrmAgent(OrmResource):
    """The class of agents"""

    __tablename__ = "agents"

    # required fields
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # optional fields
    image_url: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __mapper_args__ = {"polymorphic_identity": "agent", "with_polymorphic": "*"}

    # TODO
    # add email relationship
