import logging
import requests

from requests.exceptions import HTTPError
from typing import Iterator

from connectors.abstract.resource_connector import ResourceConnector
from connectors.record_error import RecordError
from database.model.concept.aiod_entry import AIoDEntryCreate
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create
from database.model.agent.organisation import Organisation
from database.model.agent.contact import Contact
from database.model.agent.location import LocationORM, AddressORM, GeoORM
from connectors.resource_with_relations import ResourceWithRelations


class AI4EuropeCmsOrganisationConnector(ResourceConnector[Organisation]):
    @property
    def resource_class(self) -> type[Organisation]:
        return Organisation

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.ai4europe_cms

    def run(
        self, state: dict, **kwargs
    ) -> Iterator[ResourceWithRelations[Organisation] | RecordError]:
        """Fetch resources and update the state"""

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
            pydantic_class_contact = resource_create(Contact)
            pydantic_class = resource_create(Organisation)
            contact_data = organisation["contact_details"]

            yield ResourceWithRelations[Organisation](
                resource=pydantic_class(
                    aiod_entry=(
                        AIoDEntryCreate()
                        if (
                            organisation.get("contact_details") is not None
                            and organisation["contact_details"].get("aiod_entry") is not None
                        )
                        else None
                    ),
                    platform_resource_identifier=(
                        organisation["platform_resource_identifier"]
                        if organisation.get("platform_resource_identifier") is not None
                        else None
                    ),
                    platform=organisation["platform"]
                    if organisation.get("platform") is not None
                    else None,
                    name=organisation["name"] if organisation.get("name") is not None else None,
                    date_published=organisation["date_published"]
                    if organisation.get("date_published") is not None
                    else None,
                    scientific_domain=[sd for sd in organisation.get("scientific_domain")]
                    if organisation.get("scientific_domain") is not None
                    else [],
                    industrial_sector=[ins for ins in organisation.get("industrial_sector")]
                    if organisation.get("industrial_sector") is not None
                    else [],
                    relevant_link=[rl for rl in organisation.get("relevant_link")]
                    if organisation.get("relevant_link") is not None
                    else [],
                    alternate_name=[an for an in organisation.get("alternate_name")]
                    if organisation.get("alternate_name") is not None
                    else [],
                    application_area=[ar for ar in organisation.get("application_area")]
                    if organisation.get("application_area") is not None
                    else [],
                    keyword=[k for k in organisation.get("keyword")]
                    if organisation.get("keyword") is not None
                    else [],
                    same_as=organisation["same_as"]
                    if organisation.get("same_as") is not None
                    else None,
                    legal_name=organisation["legal_name"]
                    if organisation.get("legal_name") is not None
                    else None,
                    ai_relevance=organisation["ai_relevance"]
                    if organisation.get("ai_relevance") is not None
                    else None,
                    type=organisation["type"] if organisation.get("type") is not None else None,
                ),
                resource_ORM_class=Organisation,
                related_resources={
                    "contact": [
                        pydantic_class_contact(
                            name=contact_data["name"]
                            if contact_data.get("name") is not None
                            else None,
                            platform=contact_data["platform"]
                            if contact_data.get("platform") is not None
                            else None,
                            platform_resource_identifier=(
                                contact_data["platform_resource_identifier"]
                                if contact_data.get("platform_resource_identifier") is not None
                                else None
                            ),
                            email=(
                                [e for e in contact_data["email"] if e is not None]
                                if contact_data.get("email") is not None
                                else []
                            ),
                            location=[
                                LocationORM(
                                    geo=GeoORM(
                                        latitude=(
                                            loc["geo"]["latitude"]
                                            if loc.get("geo") is not None
                                            and loc["geo"].get("latitude") is not None
                                            else None
                                        ),
                                        longitude=(
                                            loc["geo"]["longitude"]
                                            if loc.get("geo") is not None
                                            and loc["geo"].get("longitude") is not None
                                            else None
                                        ),
                                        elevation_millimeters=(
                                            loc["geo"]["elevation_millimeters"]
                                            if loc.get("geo") is not None
                                            and loc["geo"].get("elevation_millimeters") is not None
                                            else None
                                        ),
                                    ),
                                    address=AddressORM(
                                        region=(
                                            loc["address"]["region"]
                                            if loc.get("address") is not None
                                            and loc["address"].get("region") is not None
                                            else None
                                        ),
                                        locality=(
                                            loc["address"]["locality"]
                                            if loc.get("address") is not None
                                            and loc["address"].get("locality") is not None
                                            else None
                                        ),
                                        street=(
                                            loc["address"]["street"]
                                            if loc.get("address") is not None
                                            and loc["address"].get("street") is not None
                                            else None
                                        ),
                                        postal_code=(
                                            loc["address"]["postal_code"]
                                            if loc.get("address") is not None
                                            and loc["address"].get("postal_code") is not None
                                            else None
                                        ),
                                        address=(
                                            loc["address"]["address"]
                                            if loc.get("address") is not None
                                            and loc["address"].get("address") is not None
                                            else None
                                        ),
                                        country=(
                                            loc["address"]["country"]
                                            if loc.get("address") is not None
                                            and loc["address"].get("country") is not None
                                            else None
                                        ),
                                    ),
                                )
                                for loc in contact_data["location"]
                                if loc is not None
                            ]
                            if contact_data.get("location") is not None
                            else [],
                        )
                    ]
                },
            )
