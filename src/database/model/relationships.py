"""
Together with the serializers and the resource_read_and_create, this adds additional
functionality on top of SQLModel so that a model only needs to be defined once, but supports
serialization and complex relationships.
"""

import abc
import dataclasses
from typing import Any

from pydantic.utils import Representation
from sqlmodel import Field

from database.model.serializers import Serializer, DeSerializer


def ResourceRelationshipList(*args, **kwargs) -> Any:
    """
    Describing many-to-many and one-to-many relationships.

    Wrapper around the class ResourceRelationshipInfo` to keep mypy happy. Similarly used to
    the function Relationship of Pydantic.
    """
    return ResourceRelationshipListInfo(*args, **kwargs)


def ResourceRelationshipSingle(*args, **kwargs) -> Any:
    """
    Describing many-to-one relationships.

    Wrapper around the class ResourceRelationshipInfo` to keep mypy happy. Similarly used to
    the function Relationship of Pydantic.
    """
    return ResourceRelationshipSingleInfo(*args, **kwargs)


@dataclasses.dataclass
class ResourceRelationshipInfo(abc.ABC, Representation):
    """
    For many-to-one relationships
    """

    serializer: Serializer | None = None
    deserializer: DeSerializer | None = None
    description: str | None = None
    include_in_create: bool = True
    default_factory_orm: Any | None = None
    default_factory_pydantic: Any | None = None
    class_read: Any | None = None  # only needed if class_read differs from class_create
    class_create: Any | None = None  # only needed if class_read differs from class_create

    def field(self):
        return Field(
            description=self.description,
            schema_extra={"example": self.example},
            default_factory=self.default_factory_pydantic,
        )

    @property
    @abc.abstractmethod
    def example(self):
        pass


@dataclasses.dataclass
class ResourceRelationshipListInfo(ResourceRelationshipInfo):
    """For many-to-many and one-to-many relationships."""

    example: list[str] | list[int] | None = None


@dataclasses.dataclass
class ResourceRelationshipSingleInfo(ResourceRelationshipInfo):
    """For many-to-one relationships"""

    identifier_name: str | None = None
    example: str | int | None = None
