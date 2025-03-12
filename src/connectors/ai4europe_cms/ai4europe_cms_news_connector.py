import requests

from requests.exceptions import HTTPError
from typing import Iterator

from connectors.abstract.resource_connector import ResourceConnector
from connectors.record_error import RecordError
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create
from database.model.news.news import News
from connectors.resource_with_relations import ResourceWithRelations


class AI4EuropeCmsNewsConnector(ResourceConnector[News]):
    @property
    def resource_class(self) -> type[News]:
        return News

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.ai4europe_cms

    def run(self, state: dict, **kwargs) -> Iterator[ResourceWithRelations[News] | RecordError]:
        """Fetch resources and update the state"""

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
            pydantic_class = resource_create(News)

            yield ResourceWithRelations[News](
                resource=pydantic_class(
                    platform_resource_identifier=(
                        n["platform_resource_identifier"]
                        if n.get("platform_resource_identifier") is not None
                        else None
                    ),
                    platform=n["platform"] if n.get("platform") is not None else None,
                    name=n["name"] if n.get("name") is not None else None,
                    date_published=n["date_published"]
                    if n.get("date_published") is not None
                    else None,
                    headline=n["headline"] if n.get("headline") is not None else None,
                    alternative_headline=n["alternative_headline"]
                    if n.get("alternative_headline") is not None
                    else None,
                    category=[cat for cat in n["category"]]
                    if n.get("category") is not None
                    else [],
                    source=n["source"] if n.get("source") is not None else None,
                    scientific_domain=[sd for sd in n.get("scientific_domain")]
                    if n.get("scientific_domain") is not None
                    else [],
                    industrial_sector=[ins for ins in n.get("industrial_sector")]
                    if n.get("industrial_sector") is not None
                    else [],
                    relevant_link=[rl for rl in n.get("relevant_link")]
                    if n.get("relevant_link") is not None
                    else [],
                    alternate_name=[an for an in n.get("alternate_name")]
                    if n.get("alternate_name") is not None
                    else [],
                    application_area=[ar for ar in n.get("application_area")]
                    if n.get("application_area") is not None
                    else [],
                    keyword=[k for k in n.get("keyword")] if n.get("keyword") is not None else [],
                    same_as=n["same_as"] if n.get("same_as") is not None else None,
                ),
                resource_ORM_class=News,
            )
