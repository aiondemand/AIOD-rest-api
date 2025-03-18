import logging
import requests

from requests.exceptions import HTTPError
from typing import Iterator

from connectors.abstract.resource_connector_by_id import ResourceConnectorById
from connectors.record_error import RecordError
from database.model.concept.aiod_entry import AIoDEntryCreate
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create
from database.model.agent.organisation import Organisation
from database.model.agent.contact import Contact
from database.model.agent.location import LocationORM, AddressORM, GeoORM
from connectors.resource_with_relations import ResourceWithRelations


class AI4EuropeCmsOrganisationConnector(ResourceConnectorById[Organisation]):
    @property
    def resource_class(self) -> type[Organisation]:
        return Organisation

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.ai4europe_cms

    def retry(self, identifier: int):
        raise NotImplementedError("Not implemented.")

    def fetch(
        self, offset: int, from_identifier: int
    ) -> Iterator[ResourceWithRelations[Organisation] | RecordError]:

        url_data = "https://community-dev-api.aiod.eu/api/organisations/"

        headers = {"AuthorizationToken": "1234567890"}

        response = requests.get(url_data, headers=headers, timeout=600)

        if not response.ok:
            status_code = response.status_code
            msg = response.json()["error"]["message"]
            err_msg = f"Error while fetching {url_data} from AI4Europe CMS: ({status_code}) {msg}"
            logging.error(err_msg)
            err = HTTPError(err_msg)
            yield RecordError(identifier=None, error=err)
            return

        try:
            organisations = response.json()
        except Exception as e:
            yield RecordError(identifier=None, error=e)
            return

        for organisation in organisations:
            identifier = int(organisation.get("platform_resource_identifier")[5:])
            if identifier < from_identifier:
                continue

            pydantic_class_contact = resource_create(Contact)
            pydantic_class = resource_create(Organisation)
            contact_data = organisation["contact_details"]

            yield ResourceWithRelations[Organisation](
                resource=pydantic_class(
                    aiod_entry=AIoDEntryCreate()
                    if organisation.get("contact_details", {}).get("aiod_entry")
                    else None,
                    platform_resource_identifier=organisation.get("platform_resource_identifier")[
                        5:
                    ],
                    platform=organisation.get("platform"),
                    name=organisation.get("name"),
                    date_published=organisation.get("date_published"),
                    scientific_domain=organisation.get("scientific_domain", []),
                    industrial_sector=organisation.get("industrial_sector", []),
                    relevant_link=organisation.get("relevant_link", []),
                    alternate_name=organisation.get("alternate_name", []),
                    application_area=organisation.get("application_area", []),
                    keyword=organisation.get("keyword", []),
                    same_as=organisation.get("same_as"),
                    legal_name=organisation.get("legal_name"),
                    ai_relevance=organisation.get("ai_relevance"),
                    type=organisation.get("type"),
                ),
                resource_ORM_class=Organisation,
                related_resources={
                    "contact": [
                        pydantic_class_contact(
                            name=contact_data.get("name"),
                            platform=contact_data.get("platform"),
                            platform_resource_identifier=contact_data.get(
                                "platform_resource_identifier"
                            )[5:],
                            email=[e for e in contact_data.get("email", []) if e is not None],
                            location=[
                                LocationORM(
                                    geo=GeoORM(
                                        latitude=(loc.get("geo") or {}).get("latitude"),
                                        longitude=(loc.get("geo") or {}).get("longitude"),
                                        elevation_millimeters=(loc.get("geo") or {}).get(
                                            "elevation_millimeters"
                                        ),
                                    ),
                                    address=AddressORM(
                                        region=(loc.get("address") or {}).get("region"),
                                        locality=(loc.get("address") or {}).get("locality"),
                                        street=(loc.get("address") or {}).get("street"),
                                        postal_code=(loc.get("address") or {}).get("postal_code"),
                                        address=(loc.get("address") or {}).get("address"),
                                        country=(loc.get("address") or {}).get("country"),
                                    ),
                                )
                                for loc in contact_data.get("location", [])
                                if loc is not None
                            ],
                        )
                    ]
                },
            )
