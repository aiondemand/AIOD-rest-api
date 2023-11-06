"""
Together with the serializers and the resource_read_and_create, this adds additional
functionality on top of SQLModel so that a model only needs to be defined once, but supports
serialization and complex relationships.

See src/README.md for additional information.
"""

import abc
import dataclasses
import typing
from types import UnionType
from typing import Any, Type, Callable

from pydantic.utils import Representation
from sqlmodel import Field, SQLModel

from database.deletion import triggers
from database.model import serializers


@dataclasses.dataclass
class _ResourceRelationship(abc.ABC, Representation):
    """
    Configuration for handling relationships to another table.

    Args:
        serializer (Serializer): will be used to serialize the related entity into json.
        deserializer (DeSerializer): will be used to deserialize the related entity from json.
        description: (str): a description of the relation. Will be shown in Swagger if the
            related entity is serialized into a field such as a string.
        include_in_create (bool): if False, this relationship will be omitted on POSTS/PUTS,
            and only shown on GET.
        default_factory_orm: if a value is not included in create, this factory can be used to
            set a default value.
        default_factory_pydantic: a default value shown in swagger.
        class_read: normally not needed, only needed if you want to differentiate between
            class_read and class_create
        class_create: normally not needed, only needed if you want to differentiate between
            class_read and class_create
    """

    serializer: serializers.Serializer | None = None
    deserializer: serializers.DeSerializer | None = None
    description: str | None = None
    include_in_create: bool = True
    default_factory_orm: Any | None = None
    default_factory_pydantic: Any | None = None
    class_read: Any | None = None
    class_create: Any | None = None
    """jos"""

    def field(self):
        return Field(
            description=self.description,
            schema_extra={"example": self.example} if self.example is not None else None,
            default_factory=self.default_factory_pydantic,
        )

    @property
    @abc.abstractmethod
    def example(self):
        pass

    @abc.abstractmethod
    def create_triggers(self, parent_class: Type[SQLModel], field_name: str):
        pass


@dataclasses.dataclass
class _ResourceRelationshipSingle(_ResourceRelationship):
    """
    Configuration for handling one-to-one and many-to-one relationships to another table.

    Args:
        identifier_name(str): the name of the foreign key field to another table. Only fill this
        in if the related object is serialized to this identifier. Omit this value on casting
        serialization.
        example(str|int): an example value to be shown in Swagger
    """

    identifier_name: str | None = None
    """blabla"""
    example: str | int | None = None


@dataclasses.dataclass
class _ResourceRelationshipList(_ResourceRelationship):
    """
    Configuration for handling one-to-many and many-to-many relationships to another table.

    Args:
        example(Any): an example value to be shown in Swagger
    """

    example: list[Any] | None = None


@dataclasses.dataclass
class OneToOne(_ResourceRelationshipSingle):
    """
    Configuration for handling one-to-many relationships to another table.

    Args:
        on_delete_trigger_deletion_by(str): if you want to automatically delete instances of the
            other table, you can! We assume the other table has an .identifier. This field should
            then contain the name of the foreign key field the other table.

    """

    on_delete_trigger_deletion_by: None | str = None

    def create_triggers(self, parent_class: Type[SQLModel], field_name: str):
        if self.on_delete_trigger_deletion_by is not None:
            to_delete = parent_class.__annotations__[field_name]
            is_optional = typing.get_origin(to_delete) in (typing.Union, UnionType) and type(
                None
            ) in typing.get_args(to_delete)
            if is_optional:
                (to_delete,) = [
                    type_ for type_ in to_delete.__args__ if not isinstance(None, type_)
                ]
            triggers.create_deletion_trigger_one_to_one(
                trigger=parent_class,
                trigger_identifier_link=self.on_delete_trigger_deletion_by,
                to_delete=to_delete,
            )


@dataclasses.dataclass
class ManyToOne(_ResourceRelationshipSingle):
    """
    Configuration for handling many-to-one relationships to another table.

    Args:
        on_delete_trigger_deletion_of_orphan(Type[SQLModel]): automatically delete orphans of the
            related table that are not referenced anymore.
    """

    on_delete_trigger_deletion_of_orphan: None | Type[SQLModel] = None

    def create_triggers(self, parent_class: Type[SQLModel], field_name: str):
        if self.on_delete_trigger_deletion_of_orphan is not None:
            to_delete_identifier = getattr(
                parent_class.RelationshipConfig, field_name
            ).identifier_name
            triggers.create_deletion_trigger_many_to_one(
                trigger=parent_class,
                to_delete=self.on_delete_trigger_deletion_of_orphan,
                trigger_identifier_link=to_delete_identifier,
            )


@dataclasses.dataclass
class OneToMany(_ResourceRelationshipList):
    """
    Configuration for handling one-to-many relationships to another table.
    """

    def create_triggers(self, parent_class: Type[SQLModel], field_name: str):
        """No deletion triggers: thus far, this could always be solved using a cascading delete."""


@dataclasses.dataclass
class ManyToMany(_ResourceRelationshipList):
    """
    Configuration for handling many-to-one relationships to another table.

    Args:
        on_delete_trigger_orphan_deletion(Callable): automatically delete orphans of the
            related table that are not referenced anymore. This callable should return a list of
            linking-table-names that should be checked for references.
    """

    on_delete_trigger_orphan_deletion: None | Callable[[], list[str]] = None

    def create_triggers(self, parent_class: Type[SQLModel], field_name: str):
        if self.on_delete_trigger_orphan_deletion is not None:
            link = parent_class.__sqlmodel_relationships__[field_name].link_model
            to_delete = parent_class.__annotations__[field_name].__args__[0]
            other_links = self.on_delete_trigger_orphan_deletion()
            triggers.create_deletion_trigger_many_to_many(
                trigger=parent_class, link=link, to_delete=to_delete, other_links=other_links
            )
