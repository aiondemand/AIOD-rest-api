import requests

from requests.exceptions import HTTPError
from typing import Iterator

from connectors.abstract.resource_connector_by_id import ResourceConnectorById
from connectors.record_error import RecordError
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create
from database.model.event.event import Event
from connectors.resource_with_relations import ResourceWithRelations
from database.model.ai_resource.text import Text


class AI4EuropeCmsEventConnector(ResourceConnectorById[Event]):
    @property
    def resource_class(self) -> type[Event]:
        return Event

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.ai4europe_cms

    def retry(self, identifier: int):
        raise NotImplementedError("Not implemented.")

    def fetch(
        self, offset: int, from_identifier: int
    ) -> Iterator[ResourceWithRelations[Event] | RecordError]:
        url_data = "https://community-dev-api.aiod.eu/api/events/"

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
            events = response.json()
        except Exception as e:
            yield RecordError(identifier=None, error=e)
            return

        for event in events:
            identifier = int(event.get("platform_resource_identifier")[5:])
            if identifier < from_identifier:
                continue
            pydantic_class = resource_create(Event)
            yield ResourceWithRelations[Event](
                resource=pydantic_class(
                    platform_resource_identifier=event.get(
                        "platform_resource_identifier"
                    )[5:],
                    platform=event.get("platform"),
                    name=event.get("name"),
                    date_published=event.get("date_published"),
                    start_date=event.get("start_date"),
                    end_date=event.get("end_date"),
                    registration_link=event.get("registration_link")
                    if event.get("registration_link")
                    and len(event.get("registration_link")) <= 256
                    else None,
                    mode=event.get("mode"),
                    scientific_domain=event.get("scientific_domain", []),
                    industrial_sector=event.get("industrial_sector", []),
                    relevant_link=event.get("relevant_link", []),
                    alternate_name=event.get("alternate_name", []),
                    application_area=event.get("application_area", []),
                    keyword=event.get("keyword", []),
                    same_as=event.get("same_as"),
                    description=Text(
                        plain=event.get("description", {}).get("plain", ""),
                        html=event.get("description", {}).get("html", ""),
                    ),
                ),
                resource_ORM_class=Event,
            )
