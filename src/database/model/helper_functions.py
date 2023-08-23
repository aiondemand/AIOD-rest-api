from collections import ChainMap
from typing import Type, TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import SQLModel, Field

if TYPE_CHECKING:
    from database.model.relationships import ResourceRelationshipInfo


def all_annotations(cls) -> ChainMap:
    """Returns a dictionary-like ChainMap that includes annotations for all
    attributes defined in cls or inherited from superclasses.

    From
    https://stackoverflow.com/questions/63903901/how-can-i-access-to-annotations-of-parent-class
    """
    return ChainMap(*(c.__annotations__ for c in cls.__mro__ if "__annotations__" in c.__dict__))


def link_factory(table_from: str, table_to: str, table_prefix=None):
    """Create a table linking table_name_from to table_name_to, using the .identifier at both
    sides.
    """
    prefix = "" if table_prefix is None else f"{table_prefix}_"

    class LinkTable(SQLModel, table=True):  # type: ignore [call-arg]
        __tablename__ = f"{prefix}{table_from}_{table_to}_link"
        from_identifier: int = Field(
            sa_column=Column(
                Integer,
                ForeignKey(table_from + ".identifier", ondelete="CASCADE"),
                primary_key=True,
            )
        )
        linked_identifier: int = Field(foreign_key=table_to + ".identifier", primary_key=True)

    LinkTable.__name__ = LinkTable.__qualname__ = LinkTable.__tablename__
    return LinkTable


def get_relationships(resource_class: Type[SQLModel]) -> dict[str, "ResourceRelationshipInfo"]:
    if not hasattr(resource_class, "RelationshipConfig"):
        return {}
    config = resource_class.RelationshipConfig
    return {field: getattr(config, field) for field in dir(config) if not field.startswith("_")}
