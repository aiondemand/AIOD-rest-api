"""
This module knows how to load an OpenML object based on its AIoD implementation,
and how to convert the OpenML response to some agreed AIoD format.
"""
import logging
from typing import Iterator

import dateutil.parser
import requests
from fastapi import HTTPException
from sqlmodel import SQLModel

from connectors.abstract.resource_connector import ResourceConnector
from database.model.ai_asset.distribution import Distribution
from database.model.dataset.dataset import Dataset
from database.model.resource_read_and_create import resource_create
from database.model.platform.platform_names import PlatformName


class OpenMlDatasetConnector(ResourceConnector[Dataset]):
    @property
    def resource_class(self) -> type[Dataset]:
        return Dataset

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.openml

    def fetch(self, platform_identifier: str) -> SQLModel:
        url_data = f"https://www.openml.org/api/v1/json/data/{platform_identifier}"
        response = requests.get(url_data)
        if not response.ok:
            code = response.status_code
            if code == 412 and response.json()["error"]["message"] == "Unknown dataset":
                code = 404
            msg = response.json()["error"]["message"]
            raise HTTPException(
                status_code=code,
                detail=f"Error while fetching data from OpenML: '{msg}'.",
            )
        dataset_json = response.json()["data_set_description"]

        # Here we can format the response into some standardized way, maybe this includes some
        # dataset characteristics. These need to be retrieved separately from OpenML:
        url_qual = f"https://www.openml.org/api/v1/json/data/qualities/{platform_identifier}"
        response = requests.get(url_qual)
        if not response.ok:
            msg = response.json()["error"]["message"]
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error while fetching data qualities from OpenML: '{msg}'.",
            )

        qualities_json = {
            quality["name"]: quality["value"]
            for quality in response.json()["data_qualities"]["quality"]
        }
        pydantic_class = resource_create(Dataset)
        return pydantic_class(
            platform=self.platform_name,
            platform_identifier=platform_identifier,
            name=dataset_json["name"],
            same_as=url_data,
            description=dataset_json["description"],
            date_published=dateutil.parser.parse(dataset_json["upload_date"]),
            date_modified=dateutil.parser.parse(dataset_json["processing_date"]),
            distributions=[
                Distribution(
                    content_url=dataset_json["url"], encoding_format=dataset_json["format"]
                )
            ],
            size=_as_int(qualities_json["NumberOfInstances"]),
            is_accessible_for_free=True,
            keywords=[tag for tag in dataset_json["tag"]],
            license=dataset_json["licence"] if "licence" in dataset_json else None,
            version=dataset_json["version"],
            alternate_names=[],
            citations=[],
            is_part=[],
            has_parts=[],
            measured_values=[],
        )

    def fetch_all(self, limit: int | None = None) -> Iterator[SQLModel]:
        url = "https://www.openml.org/api/v1/json/data/list"
        if limit is not None:
            url = f"{url}/limit/{limit}"
        response = requests.get(url)
        response_json = response.json()
        if not response.ok:
            msg = response_json["error"]["message"]
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error while fetching data list from OpenML: '{msg}'.",
            )
        for dataset_json in response_json["data"]["dataset"]:
            try:
                yield self.fetch(dataset_json["did"])
            except Exception as e:
                logging.error(
                    f"Error while fetching openml  dataset {dataset_json['did']}: '{str(e)}'"
                )


def _as_int(v: str) -> int:
    as_float = float(v)
    if not as_float.is_integer():
        raise ValueError(f"The input should be an integer, but was a float: {v}")
    return int(as_float)
