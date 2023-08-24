import abc
from typing import Generic, TypeVar, Type

from sqlmodel import SQLModel, Session

RESOURCE = TypeVar("RESOURCE", bound=SQLModel)
SCHEMA_CLASS = TypeVar("SCHEMA_CLASS")


class SchemaConverter(abc.ABC, Generic[RESOURCE, SCHEMA_CLASS]):
    """Converting between our AIoD representation of a resource and another representation. For
    example, for dataset, we can convert it to schema.org or DCAT-AP formats.

    This makes it easier for other services to connect to AIoD. Instead of adapting to the AIoD
    schema, they can use existing standards.
    """

    @property
    @abc.abstractmethod
    def to_class(self) -> Type[SCHEMA_CLASS]:
        pass

    @abc.abstractmethod
    def convert(self, session: Session, aiod: RESOURCE) -> SCHEMA_CLASS:
        pass
