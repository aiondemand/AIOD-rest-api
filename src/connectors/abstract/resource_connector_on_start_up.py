import abc
import datetime
import logging
from typing import Generic, Iterator

from connectors.abstract.resource_connector import ResourceConnector, RESOURCE
from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations


class ResourceConnectorOnStartUp(ResourceConnector, Generic[RESOURCE]):
    """A connector that only runs once, on startup, and performs no synchronization later."""

    @abc.abstractmethod
    def fetch(
        self, limit: int | None = None
    ) -> Iterator[RESOURCE | ResourceWithRelations[RESOURCE] | RecordError]:
        """Retrieve information of all resources"""

    def run(
        self, state: dict, limit: int | None = None, **kwargs
    ) -> Iterator[RESOURCE | ResourceWithRelations[RESOURCE] | RecordError]:
        if state:
            logging.warning("This connector has run before. Exiting.")
            return
        if limit is not None:
            logging.warning(
                "Limiting the results! Please remove the limit command line argument "
                "in production."
            )
        state["result"] = f"started on {datetime.datetime.now()}"
        yield from self.fetch(limit=limit)
        state["result"] = "Complete run done (although there might be errors)."
