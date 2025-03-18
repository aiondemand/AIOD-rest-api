import requests

from requests.exceptions import HTTPError
from typing import Iterator

from connectors.abstract.resource_connector_by_id import ResourceConnectorById
from connectors.record_error import RecordError
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create
from database.model.news.news import News
from connectors.resource_with_relations import ResourceWithRelations


class AI4EuropeCmsNewsConnector(ResourceConnectorById[News]):
    @property
    def resource_class(self) -> type[News]:
        return News

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.ai4europe_cms

    def retry(self, identifier: int):
        raise NotImplementedError("Not implemented.")

    def fetch(
        self, offset: int, from_identifier: int
    ) -> Iterator[ResourceWithRelations[News] | RecordError]:
        url_data = "https://community-dev-api.aiod.eu/api/news/"

        headers = {"AuthorizationToken": "1234567890"}

        response = requests.get(url_data, headers=headers, timeout=600)

        if not response.ok:
            status_code = response.status_code
            msg = response.json()["error"]["message"]
            err_msg = f"Error while fetching {url_data} from AI4Europe CMS: ({status_code}) {msg}"
            err = HTTPError(err_msg)
            yield RecordError(identifier=None, error=err)
            return

        try:
            news = response.json()
        except Exception as e:
            yield RecordError(identifier=None, error=e)
            return

        for n in news:
            identifier = int(n.get("platform_resource_identifier")[5:])
            if identifier < from_identifier:
                continue

            pydantic_class = resource_create(News)
            yield ResourceWithRelations[News](
                resource=pydantic_class(
                    platform_resource_identifier=n.get("platform_resource_identifier")[5:],
                    platform=n.get("platform"),
                    name=n.get("name"),
                    date_published=n.get("date_published"),
                    headline=n.get("headline"),
                    alternative_headline=n.get("alternative_headline"),
                    category=n.get("category", []),
                    source=n.get("source"),
                    scientific_domain=n.get("scientific_domain", []),
                    industrial_sector=n.get("industrial_sector", []),
                    relevant_link=n.get("relevant_link", []),
                    alternate_name=n.get("alternate_name", []),
                    application_area=n.get("application_area", []),
                    keyword=n.get("keyword", []),
                    same_as=n.get("same_as"),
                ),
                resource_ORM_class=News,
            )
