import json
import pathlib
from typing import Iterator, TypeVar

from connectors.abstract.resource_connector_on_start_up import ResourceConnectorOnStartUp
from database.model.named_relation import NamedRelation
from database.model.platform.platform_names import PlatformName

RESOURCE = TypeVar("RESOURCE", bound=NamedRelation)


class EnumConnector(ResourceConnectorOnStartUp[RESOURCE]):
    """
    Filling enums using a hard-coded json
    """

    def __init__(self, json_path: pathlib.Path, resource_class: type[RESOURCE]):
        self.json_path = json_path
        self._resource_class = resource_class

    @property
    def resource_class(self) -> type[RESOURCE]:
        return self._resource_class

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.example

    def fetch(self, limit: int | None = None) -> Iterator[RESOURCE]:
        with open(self.json_path) as f:
            json_data = json.load(f)
        yield from json_data[:limit]
