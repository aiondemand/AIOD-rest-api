import json
import pathlib
from typing import Iterator, TypeVar

from sqlmodel import SQLModel

from connectors.abstract.resource_connector_on_start_up import ResourceConnectorOnStartUp
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create

RESOURCE = TypeVar("RESOURCE", bound=SQLModel)


class ExampleConnector(ResourceConnectorOnStartUp[RESOURCE]):
    """
    Creating hardcoded values example values based on json files
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
        pydantic_class = resource_create(self.resource_class)
        for json_item in json_data[:limit]:
            yield pydantic_class(**json_item)
