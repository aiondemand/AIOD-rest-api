import requests

from requests.exceptions import HTTPError
from typing import Iterator

from connectors.abstract.resource_connector import ResourceConnector
from connectors.record_error import RecordError
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create
from database.model.event.event import Event
from connectors.resource_with_relations import ResourceWithRelations
from database.model.ai_resource.text import Text


class AI4EuropeCmsEventConnector(ResourceConnector[Event]):
    @property
    def resource_class(self) -> type[Event]:
        return Event

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.ai4europe_cms

    def run(self, state: dict, **kwargs) -> Iterator[ResourceWithRelations[Event] | RecordError]:
        """Fetch resources and update the state"""

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
            pydantic_class = resource_create(Event)
            desc = event.get("description") or {}

            yield ResourceWithRelations[Event](
                resource=pydantic_class(
                    platform_resource_identifier=(
                        event["platform_resource_identifier"]
                        if event.get("platform_resource_identifier") is not None
                        else None
                    ),
                    platform=event["platform"] if event.get("platform") is not None else None,
                    name=event["name"] if event.get("name") is not None else None,
                    date_published=event["date_published"]
                    if event.get("date_published") is not None
                    else None,
                    start_date=event["start_date"] if event.get("start_date") is not None else None,
                    end_date=event["end_date"] if event.get("end_date") is not None else None,
                    registration_link=event["registration_link"]
                    if event.get("registration_link") is not None
                    and len(event.get("registration_link")) <= 256
                    else None,
                    mode=event["mode"] if event.get("mode") is not None else None,
                    scientific_domain=[sd for sd in event.get("scientific_domain")]
                    if event.get("scientific_domain") is not None
                    else [],
                    industrial_sector=[ins for ins in event.get("industrial_sector")]
                    if event.get("industrial_sector") is not None
                    else [],
                    relevant_link=[rl for rl in event.get("relevant_link")]
                    if event.get("relevant_link") is not None
                    else [],
                    alternate_name=[an for an in event.get("alternate_name")]
                    if event.get("alternate_name") is not None
                    else [],
                    application_area=[ar for ar in event.get("application_area")]
                    if event.get("application_area") is not None
                    else [],
                    keyword=[k for k in event.get("keyword")]
                    if event.get("keyword") is not None
                    else [],
                    same_as=event["same_as"] if event.get("same_as") is not None else None,
                    description=Text(
                        plain=desc.get("plain") or "",
                        html=desc.get("html") or "",
                    ),
                ),
                resource_ORM_class=Event,
            )
