"""
This module knows how to load an OpenML object based on its AIoD implementation,
and how to convert the OpenML response to some agreed AIoD format.
"""
from typing import Iterator

import dateutil.parser
import requests
from sqlmodel import SQLModel

from connectors.abstract.resource_connector_by_id import ResourceConnectorById
from connectors.record_error import RecordError
from database.model import field_length
from database.model.ai_asset.distribution import Distribution
from database.model.concept.aiod_entry import AIoDEntryCreate
from database.model.dataset.dataset import Dataset
from database.model.dataset.size import DatasetSize
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create


class OpenMlDatasetConnector(ResourceConnectorById[Dataset]):
    """
    Openml does not allow gathering the records based on the last modified datetime. Instead,
    it does guarantee strictly ascending identifiers. This is the reason why the
    ResourceConnectorById is used.
    """

    @property
    def resource_class(self) -> type[Dataset]:
        return Dataset

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.openml

    def retry(self, identifier: int) -> SQLModel | RecordError:
        url_qual = f"https://www.openml.org/api/v1/json/data/qualities/{identifier}"
        response = requests.get(url_qual)
        if not response.ok:
            msg = response.json()["error"]["message"]
            return RecordError(
                identifier=str(identifier),
                error=f"Error while fetching data from OpenML: '{msg}'.",
            )
        qualities = response.json()["data_qualities"]["quality"]
        return self.fetch_record(identifier, qualities)

    def fetch_record(
        self, identifier: int, qualities: list[dict[str, str]]
    ) -> SQLModel | RecordError:
        url_data = f"https://www.openml.org/api/v1/json/data/{identifier}"
        response = requests.get(url_data)
        if not response.ok:
            msg = response.json()["error"]["message"]
            return RecordError(
                identifier=str(identifier),
                error=f"Error while fetching data from OpenML: '{msg}'.",
            )
        dataset_json = response.json()["data_set_description"]

        qualities_json = {quality["name"]: quality["value"] for quality in qualities}
        pydantic_class = resource_create(Dataset)
        description = dataset_json["description"]
        if isinstance(description, list) and len(description) == 0:
            description = ""
        elif not isinstance(description, str):
            return RecordError(identifier=str(identifier), error="Description of unknown format.")
        if len(description) > field_length.DESCRIPTION:
            text_break = " [...]"
            description = description[: field_length.DESCRIPTION - len(text_break)] + text_break
        size = None
        if "NumberOfInstances" in qualities_json:
            size = DatasetSize(value=_as_int(qualities_json["NumberOfInstances"]), unit="instances")
        return pydantic_class(
            aiod_entry=AIoDEntryCreate(
                platform=self.platform_name,
                platform_identifier=identifier,
            ),
            name=dataset_json["name"],
            same_as=url_data,
            description=description,
            date_published=dateutil.parser.parse(dataset_json["upload_date"]),
            distribution=[
                Distribution(
                    content_url=dataset_json["url"], encoding_format=dataset_json["format"]
                )
            ],
            size=size,
            is_accessible_for_free=True,
            keyword=[tag for tag in dataset_json["tag"]] if "tag" in dataset_json else [],
            license=dataset_json["licence"] if "licence" in dataset_json else None,
            version=dataset_json["version"],
        )

    def fetch(self, offset: int, from_identifier: int) -> Iterator[SQLModel | RecordError]:
        url_data = (
            "https://www.openml.org/api/v1/json/data/list/"
            f"limit/{self.limit_per_iteration}/offset/{offset}"
        )
        response = requests.get(url_data)
        if not response.ok:
            msg = response.json()["error"]["message"]
            yield RecordError(
                identifier=None,
                error=f"Error while fetching {url_data} from OpenML: '{msg}'.",
            )
            return

        try:
            dataset_summaries = response.json()["data"]["dataset"]
        except Exception as e:
            yield RecordError(identifier=None, error=e)
            return

        for summary in dataset_summaries:
            identifier = None
            try:
                identifier = summary["did"]
                if identifier < from_identifier:
                    yield RecordError(identifier=identifier, error="Id too low", ignore=True)
                if from_identifier is None or identifier >= from_identifier:
                    qualities = summary["quality"]
                    yield self.fetch_record(identifier, qualities)
            except Exception as e:
                yield RecordError(identifier=identifier, error=e)


def _as_int(v: str) -> int:
    as_float = float(v)
    if not as_float.is_integer():
        raise ValueError(f"The input should be an integer, but was a float: {v}")
    return int(as_float)
