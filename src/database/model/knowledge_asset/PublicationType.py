from sqlalchemy.orm import backref
from sqlmodel import Field, Relationship

from database.model.named_relation import Taxonomy
from database.model.named_relation import create_taxonomy


# class PublicationType(Taxonomy, table=True):  # type: ignore [call-arg]
#     __tablename__ = "publication_type"

PublicationType = create_taxonomy(class_name="PublicationType", table_name="publication_type")
