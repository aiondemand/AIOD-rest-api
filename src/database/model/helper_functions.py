from typing import Type, TYPE_CHECKING

from pydantic import create_model
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlmodel import SQLModel, Field

from database.model.field_length import IDENTIFIER_LENGTH

if TYPE_CHECKING:
    from database.model.relationships import _ResourceRelationship


def many_to_many_link_factory(
    table_from: str,
    table_to: str,
    table_prefix=None,
    table_from_identifier="identifier",
    table_to_identifier="identifier",
    from_identifier_type=int,
    to_identifier_type=int,
):
    """Create a table linking table_name_from to table_name_to, using the .identifier at both
    sides.
    """
    prefix = "" if table_prefix is None else f"{table_prefix}_"
    name = f"{prefix}{table_from}_{table_to}_link"
    str_type = String(IDENTIFIER_LENGTH)
    int_type = Integer
    LinkTable = create_model(
        name,
        __base__=(SQLModel,),
        __cls_kwargs__=dict(table=True),
        from_identifier=(
            from_identifier_type,
            Field(
                sa_column=Column(
                    str_type if from_identifier_type == str else int_type,
                    ForeignKey(
                        f"{table_from}.{table_from_identifier}",
                        ondelete="CASCADE",
                        onupdate="CASCADE",
                    ),
                    primary_key=True,
                )
            ),
        ),
        linked_identifier=(
            to_identifier_type,
            Field(
                sa_column=Column(
                    str_type if to_identifier_type == str else int_type,
                    ForeignKey(
                        f"{table_to}.{table_to_identifier}",
                        onupdate="CASCADE",
                    ),
                    primary_key=True,
                )
            ),
        ),
    )
    # Pydantic will issue a warning for non-default dunder attributes, so we add it after creation
    LinkTable.__tablename__ = name
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
