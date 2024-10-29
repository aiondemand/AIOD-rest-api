import abc
import logging
from typing import Generic, Iterator
from requests.exceptions import HTTPError

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
        # Setting offset to zero, to avoid "swiss-cheese" indexing (Issue: #372).
        # Further, offset is not required to persist in disk anymore.
        offset = 0

        if first_run and from_identifier is None:
            raise ValueError("In the first run, the from-identifier needs to be set")
        elif first_run:
            state["from_id"] = from_identifier if from_identifier is not None else 0
        else:
            state["from_id"] = state["last_id"] + 1

        logging.info(
            f"Starting synchronisation of records from id {state['from_id']} and"
            f" offset {offset}"
        )

        finished = False
        n_results = 0
        while not finished:
            i = 0
            for item in self.fetch(offset=offset, from_identifier=state["from_id"]):
                if isinstance(item, RecordError) and isinstance(item.error, HTTPError):
                    yield item
                    return
                i += 1
                if isinstance(item, ResourceWithRelations):
                    id_ = item.resource.platform_resource_identifier
                elif isinstance(item, RecordError):
                    id_ = item.identifier
                else:
                    id_ = item.platform_resource_identifier

                id_ = int(id_) if id_ else None

                if id_ is None or id_ >= state["from_id"]:
                    if id_ is not None:
                        state["last_id"] = id_
                    yield item
                    n_results += 1
                    if n_results == limit:
                        return

            finished = i < self.limit_per_iteration
            logging.info(f"Finished: {i} < {self.limit_per_iteration}")
            offset += i
        state["result"] = "Complete run done (although there might be errors)."
