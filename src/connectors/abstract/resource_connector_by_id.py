import abc
import logging
from typing import Generic, Iterator

from connectors.abstract.resource_connector import ResourceConnector, RESOURCE
from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations


class ResourceConnectorById(ResourceConnector, Generic[RESOURCE]):
    """Connectors that synchronize by filtering the results on identifier. In every subsequent run,
    only identifiers higher than the highest identifier of the previous run are fetched."""

    def __init__(self, limit_per_iteration: int = 500):
        self.limit_per_iteration = limit_per_iteration

    @abc.abstractmethod
    def retry(self, identifier: int) -> RESOURCE | ResourceWithRelations[RESOURCE] | RecordError:
        """Retrieve information of the resource identified by id"""

    @abc.abstractmethod
    def fetch(
        self, offset: int, from_identifier: int
    ) -> Iterator[RESOURCE | ResourceWithRelations[RESOURCE] | RecordError]:
        """Retrieve information of resources"""

    def run(
        self, state: dict, from_identifier: int | None = None, limit: int | None = None, **kwargs
    ) -> Iterator[RESOURCE | ResourceWithRelations[RESOURCE] | RecordError]:
        if limit is not None:
            logging.warning(
                "Limiting the results! Please remove the limit command line argument "
                "in production."
            )

        first_run = not state
        if first_run and from_identifier is None:
            raise ValueError("In the first run, the from-identifier needs to be set")
        elif first_run:
            state["offset"] = 0
            state["from_id"] = from_identifier if from_identifier is not None else 0
        else:
            state["from_id"] = state["last_id"] + 1
            state["offset"] = state["offset"]  # TODO: what if datasets are deleted? Or updated?

        logging.info(
            f"Starting synchronisation of records from id {state['from_id']} and"
            f" offset {state['offset']}"
        )

        finished = False
        n_results = 0
        while not finished:
            i = 0
            for item in self.fetch(offset=state["offset"], from_identifier=state["from_id"]):
                i += 1
                if hasattr(item, "platform_identifier") and item.platform_identifier is not None:
                    id_ = int(item.platform_identifier)
                else:
                    id_ = None
                if id_ is None or id_ >= state["from_id"]:
                    if id_ is not None:
                        state["last_id"] = id_
                    yield item
                    n_results += 1
                    if n_results == limit:
                        return

            finished = i < self.limit_per_iteration
            logging.info(f"Finished: {i} < {self.limit_per_iteration}")
            state["offset"] += i
        state["result"] = "Complete run done (although there might be errors)."
