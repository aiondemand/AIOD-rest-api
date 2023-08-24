import abc

from typing import Generic, TypeVar, Iterator

from sqlmodel import SQLModel

from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform_names import PlatformName


RESOURCE = TypeVar("RESOURCE", bound=AIoDConcept)


class ResourceConnector(abc.ABC, Generic[RESOURCE]):
    """
    For every platform that offers a resource, a subclass of the ResourceConnector should be
    implemented.
    """

    @property
    @abc.abstractmethod
    def resource_class(self) -> type[RESOURCE]:
        """The resource class that this connector fetches. E.g. Dataset."""

    @property
    @abc.abstractmethod
    def platform_name(self) -> PlatformName:
        """The platform of this connector."""

    @abc.abstractmethod
    def run(
        self, state: dict, **kwargs
    ) -> Iterator[SQLModel | ResourceWithRelations[SQLModel] | RecordError]:
        """Fetch resources and update the state"""
