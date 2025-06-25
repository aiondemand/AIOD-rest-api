from sqlalchemy.orm import backref
from sqlmodel import Field, Relationship

from database.model.named_relation import Taxonomy


class PublicationType(Taxonomy, table=True):  # type: ignore [call-arg]
    __tablename__ = "publication_type"

    # Taxonomies are hierarchical, e.g., a Cow is also a Mammal.
    parent_id: int | None = Field(
        foreign_key="publication_type.identifier", default=None, nullable=True
    )
    children: list["PublicationType"] = Relationship(
        sa_relationship_kwargs=dict(
            cascade="all",
            backref=backref("parent", remote_side="PublicationType.identifier"),
        )
    )
    # above statement also generated a `parent: Self | None` attribute if there is a parent
    # term in the taxonomy
