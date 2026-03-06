"""AIBuilder MLModel Connector
This module knows how to load an AIBuilder object from their API and to
convert the AIBuilder response to the AIoD MLModel format.
"""

import os
import pytz
import logging
import requests

from requests.exceptions import HTTPError
from starlette import status
from datetime import datetime
from ratelimit import limits, sleep_and_retry
from typing import Iterator, Tuple, Any

from config import REQUEST_TIMEOUT

from database.model.models_and_experiments.ml_model import MLModel
from database.model.platform.platform_names import PlatformName
from database.model.ai_resource.text import Text
from database.model import field_length
from database.model.models_and_experiments.runnable_distribution import RunnableDistribution
from database.model.resource_read_and_create import resource_create
from database.model.agent.contact import Contact
from database.model.concept.aiod_entry import AIoDEntryCreate

from connectors.abstract.resource_connector_by_date import ResourceConnectorByDate
from connectors.resource_with_relations import ResourceWithRelations
from connectors.record_error import RecordError

from .aibuilder_mappings import mlmodel_mapping

TOKEN = os.getenv("AIBUILDER_API_TOKEN", "")
API_URL = "https://aiexp-dev.ai4europe.eu/federation"
GLOBAL_MAX_CALLS_MINUTE = 60
GLOBAL_MAX_CALLS_HOUR = 2000
ONE_MINUTE = 60
ONE_HOUR = 3600


class AIBuilderMLModelConnector(ResourceConnectorByDate[MLModel]):
    """The class that implements the AIBuilder MLModel Connector.
    It inheritates from `ResourceConnectorByDate` because the AIBuilder
    platform entities have a `lastModified` field.
    """

    def __init__(self, token=TOKEN):
        self.token = token
        if self.token == "":
            raise ValueError(
                "You need to asign a value to AIBUILDER_API_TOKEN environment variable."
            )

    @property
    def resource_class(self) -> type[MLModel]:
        return MLModel

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.aibuilder

    def retry(self, identifier: int) -> ResourceWithRelations[MLModel] | RecordError:
        raise NotImplementedError("Not implemented.")

    @sleep_and_retry
    @limits(calls=GLOBAL_MAX_CALLS_MINUTE, period=ONE_MINUTE)
    @limits(calls=GLOBAL_MAX_CALLS_HOUR, period=ONE_HOUR)
    def get_response(self, url) -> dict | list | RecordError:
        """
        Performs the `url` request checking for correctness and returns the
        `list` or `dict`structure received or a `RecordError`.
        """
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
        except Exception as e:
            return RecordError(identifier=None, error=e)
        if response.status_code == status.HTTP_200_OK:
            return response.json()
        else:
            status_code = response.status_code
            if status_code == status.HTTP_401_UNAUTHORIZED:
                msg = "Unauthorized token."
            else:
                msg = response.reason
            err_msg = f"Error while fetching {url} from AIBuilder: ({status_code}) {msg}"
            logging.error(err_msg)
            err = HTTPError(err_msg)
            return RecordError(identifier=None, error=err)

    def _is_aware(self, date):
        """Returns True if `date` is a timezone-aware `datetime`."""
        return date.tzinfo is not None and date.tzinfo.utcoffset(date) is not None

    def _mlmodel_from_solution(  # noqa: C901
        self, solution: dict, id: str, url: str
    ) -> ResourceWithRelations[MLModel] | RecordError:
        """
        Generates an fills a `ResourceWithRelations` object with the `MlModel`
        attributes received in a `dict`.
        """

        if not set(mlmodel_mapping.values()) <= set(solution.keys()):
            err_msg = "Bad structure on the received solution."
            return RecordError(identifier=id, error=err_msg)

        identifier = ""
        if "platform_resource_identifier" in mlmodel_mapping.keys():
            identifier = solution[mlmodel_mapping["platform_resource_identifier"]]

        if not identifier:
            err_msg = "The platform identifier is mandatory."
            return RecordError(identifier=id, error=err_msg)

        if identifier != id:
            err_msg = f"The identifier {identifier} does not correspond with the fetched solution."
            return RecordError(identifier=id, error=err_msg)

        name = ""
        if "name" in mlmodel_mapping.keys():
            name = solution[mlmodel_mapping["name"]]

        if not name:
            err_msg = "The name field is mandatory."
            return RecordError(identifier=id, error=err_msg)

        date_published = ""
        if "date_published" in mlmodel_mapping.keys():
            date_published = solution[mlmodel_mapping["date_published"]]

        # TODO: Review the AIBuilder schema to map version
        version = ""
        if "version" in mlmodel_mapping.keys():
            version = solution[mlmodel_mapping["version"]]

        description = ""
        if "description" in mlmodel_mapping.keys():
            description = _description_format(solution[mlmodel_mapping["description"]])

        # TODO: Review the AIBuilder schema to map distribution
        distribution = []
        if "distribution" in mlmodel_mapping.keys():
            distribution = _distribution_format(solution[mlmodel_mapping["distribution"]])

        tags = []
        if "keyword" in mlmodel_mapping.keys():
            tags = solution[mlmodel_mapping["keyword"]]

        # TODO: Review the AIBuilder schema to map license
        license = ""
        if "license" in mlmodel_mapping.keys():
            license = solution[mlmodel_mapping["license"]]

        related_resources = {}

        if "contact" in mlmodel_mapping.keys():
            pydantic_class_contact = resource_create(Contact)
            contact_names = [
                pydantic_class_contact(name=name)
                for name in _as_list(solution[mlmodel_mapping["contact"]])
            ]
            related_resources["contact"] = contact_names

        if "creator" in mlmodel_mapping.keys():
            pydantic_class_creator = resource_create(Contact)
            creator_names = [
                pydantic_class_creator(name=name)
                for name in _as_list(solution[mlmodel_mapping["creator"]])
            ]
            related_resources["creator"] = creator_names

        pydantic_class = resource_create(MLModel)
        mlmodel = pydantic_class(
            platform="aibuilder",
            platform_resource_identifier=identifier,
            name=name,
            date_published=date_published,
            same_as=url,  # TODO: Review the concept of having the TOKEN inside the url!!!
            is_accessible_for_free=True,
            version=version,
            aiod_entry=AIoDEntryCreate(),
            description=description,
            distribution=distribution,
            keyword=tags,
            license=license,
        )

        return ResourceWithRelations[pydantic_class](  # type:ignore
            resource=mlmodel,
            resource_ORM_class=MLModel,
            related_resources=related_resources,
        )

    def fetch(  # noqa: C901
        self, from_incl: datetime, to_excl: datetime
    ) -> Iterator[Tuple[datetime | None, MLModel | ResourceWithRelations[MLModel] | RecordError]]:
        """
        It fetches the entire list of catalogs and, for each catalog, the entire list of solutions.
        Then it filters by date and fetches every solution within [`from_incl`, `to_excl`).
        """
        # TODO: The AIBuilder API will soon include date search for the catalog list of solutions.

        self.is_concluded = False

        if not self._is_aware(from_incl):
            from_incl = from_incl.replace(tzinfo=pytz.UTC)
        if not self._is_aware(to_excl):
            to_excl = to_excl.replace(tzinfo=pytz.UTC)

        url_get_catalog_list = f"{API_URL}/get_catalog_list?apiToken={self.token}"
        response = self.get_response(url_get_catalog_list)
        if isinstance(response, RecordError):
            self.is_concluded = True
            yield None, response
            return

        try:
            catalog_list = [catalog["catalogId"] for catalog in response]
        except Exception as e:
            self.is_concluded = True
            yield None, RecordError(identifier=None, error=e)
            return

        if len(catalog_list) == 0:
            self.is_concluded = True
            yield None, RecordError(identifier=None, error="Empty catalog list.")
            return

        for num_catalog, catalog in enumerate(catalog_list):
            url_get_catalog_solutions = (
                f"{API_URL}/get_catalog_solutions?catalogId={catalog}&apiToken={self.token}"
            )
            response = self.get_response(url_get_catalog_solutions)
            if isinstance(response, RecordError):
                self.is_concluded = num_catalog == len(catalog_list) - 1
                yield None, response
                continue

            try:
                solutions_list = [
                    solution["fullId"]
                    for solution in response
                    if from_incl <= datetime.fromisoformat(solution["lastModified"]) < to_excl
                ]
            except Exception as e:
                self.is_concluded = num_catalog == len(catalog_list) - 1
                yield None, RecordError(identifier=None, error=e)
                continue

            if len(solutions_list) == 0:
                self.is_concluded = num_catalog == len(catalog_list) - 1
                yield None, RecordError(identifier=None, error="Empty solution list.", ignore=True)
                continue

            for num_solution, solution in enumerate(solutions_list):
                url_get_solution = f"{API_URL}/get_solution?fullId={solution}&apiToken={self.token}"
                url_to_show = (
                    f"{API_URL}/get_solution?fullId={solution}&apiToken=AIBUILDER_API_TOKEN"
                )
                response = self.get_response(url_get_solution)
                if isinstance(response, RecordError):
                    self.is_concluded = (
                        num_catalog == len(catalog_list) - 1
                        and num_solution == len(solutions_list) - 1
                    )
                    yield None, response
                    continue

                try:
                    self.is_concluded = (
                        num_catalog == len(catalog_list) - 1
                        and num_solution == len(solutions_list) - 1
                    )
                    yield (
                        datetime.fromisoformat(response["lastModified"]),
                        self._mlmodel_from_solution(response, solution, url_to_show),
                    )
                except Exception as e:
                    self.is_concluded = (
                        num_catalog == len(catalog_list) - 1
                        and num_solution == len(solutions_list) - 1
                    )
                    yield None, RecordError(identifier=solution, error=e)


def _description_format(description: str) -> Text:
    """Generates a `Text` class with a plain text description from a `str`."""
    if not description:
        description = ""
    if len(description) > field_length.LONG:
        text_break = " [...]"
        description = description[: field_length.LONG - len(text_break)] + text_break
    return Text(plain=description)


# TODO: Review the AIBuilder schema to map distribution
def _distribution_format(distribution) -> list[RunnableDistribution]:
    return []


def _as_list(value: Any | list[Any]) -> list[Any]:
    """Wrap it with a list, if it is not a list"""
    if not value:
        return []
    if not isinstance(value, list):
        return [value]
    return value
