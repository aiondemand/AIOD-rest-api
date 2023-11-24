from typing import Type, TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import SQLModel, Field

if TYPE_CHECKING:
    from database.model.relationships import _ResourceRelationship


def many_to_many_link_factory(
    table_from: str,
    table_to: str,
    table_prefix=None,
    table_from_identifier="identifier",
    table_to_identifier="identifier",
):
    """Create a table linking table_name_from to table_name_to, using the .identifier at both
    sides.
    """
    prefix = "" if table_prefix is None else f"{table_prefix}_"

    class LinkTable(SQLModel, table=True):  # type: ignore [call-arg]
        __tablename__ = f"{prefix}{table_from}_{table_to}_link"
        from_identifier: int = Field(
            sa_column=Column(
                Integer,
                ForeignKey(f"{table_from}.{table_from_identifier}", ondelete="CASCADE"),
                primary_key=True,
            )
        )
        linked_identifier: int = Field(
            foreign_key=f"{table_to}.{table_to_identifier}", primary_key=True
        )

    LinkTable.__name__ = LinkTable.__qualname__ = LinkTable.__tablename__
    return LinkTable


def get_relationships(resource_class: Type[SQLModel]) -> dict[str, "_ResourceRelationship"]:
    if not hasattr(resource_class, "RelationshipConfig"):
        return {}
    config = resource_class.RelationshipConfig
    return {field: getattr(config, field) for field in dir(config) if not field.startswith("_")}


def non_abstract_subclasses(cls):
    """
    All non-abstract subclasses of the class.

    To check if a class is abstract, we check if it has any children itself. This will break if
    we ever inherit from a non-abstract class.
    """
    for child in cls.__subclasses__():
        has_grandchild = False
        for grand_child in non_abstract_subclasses(child):
            has_grandchild = True
            yield grand_child
        if not has_grandchild:
            yield child
