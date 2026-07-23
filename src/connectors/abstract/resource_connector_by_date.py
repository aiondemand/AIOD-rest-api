import abc
import logging

from datetime import datetime, timedelta, timezone
from typing import Generic, Iterator, Tuple

from connectors.abstract.resource_connector import ResourceConnector
from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations
from routers.resource_router import RESOURCE


class ResourceConnectorByDate(ResourceConnector, Generic[RESOURCE]):
    """Connectors that synchronize by filtering the results on datetime. In every subsequent run,
    the previous end-datetime is used as datetime-from."""

    is_concluded: bool

    @abc.abstractmethod
    def retry(self, _id: int) -> RESOURCE | ResourceWithRelations[RESOURCE] | RecordError:
        """Retrieve information of the resource identified by id"""

    @abc.abstractmethod
    def fetch(
        self, from_incl: datetime, to_excl: datetime
    ) -> Iterator[Tuple[datetime | None, RESOURCE | ResourceWithRelations[RESOURCE] | RecordError]]:
        """Retrieve information of all resources"""

    def run(
        self,
        state: dict,
        limit: int | None = None,
        from_incl: datetime | None = None,
        to_excl: datetime | None = None,
        time_per_loop: timedelta = timedelta(days=1),
        **kwargs,
    ) -> Iterator[RESOURCE | ResourceWithRelations[RESOURCE] | RecordError]:
        if limit is not None:
            raise ValueError(
                "Limit not implemented for this connector. Please remove the command line argument."
            )
        if to_excl is not None:
            logging.warning("to_excl should only be set in (unit) tests")
            to_excl = to_excl.replace(tzinfo=timezone.utc)
        else:
            to_excl = datetime.now(timezone.utc)

        first_run = not state
        if first_run:
            if from_incl is None:
                raise ValueError("In the first run, from_incl needs to be set")
            state["last"] = None
            from_incl = from_incl.replace(tzinfo=timezone.utc)
        else:
            last = state["last"] if state["last"] is not None else state["to_excl"]
            from_incl = datetime.fromtimestamp(last + 0.001, timezone.utc)

        while from_incl < to_excl:
            to_excl_current = min(from_incl + time_per_loop, to_excl)
            logging.info(f"Starting synchronisation {from_incl=}, {to_excl_current=}.")
            state["from_incl"] = from_incl.timestamp()
            state["to_excl"] = to_excl_current.timestamp()
            for datetime_, result in self.fetch(from_incl=from_incl, to_excl=to_excl_current):
                yield result
                if datetime_:
                    state["last"] = datetime_.timestamp()
            from_incl = (
                to_excl_current
                if self.is_concluded or state["last"] is None
                else datetime.fromtimestamp(state["last"] + 0.001, timezone.utc)
            )

        state["result"] = "Complete run done (although there might be errors)."
