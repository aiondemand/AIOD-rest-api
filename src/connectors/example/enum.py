from typing import Iterator, TypeVar

from sqlmodel import SQLModel

from connectors.abstract.resource_connector_on_start_up import ResourceConnectorOnStartUp
from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations
from database.model.ai_resource.application_area import ApplicationArea
from database.model.educational_resource.educational_resource_type import (
    EducationalResourceType,
)
from database.model.event.event import EventMode, EventStatus
from database.model.agent.language import Language
from database.model.ai_asset.license import License
from database.model.agent.organisation import OrganisationType
from database.model.news.news_category import NewsCategory
from database.model.platform.platform_names import PlatformName

RESOURCE = TypeVar("RESOURCE", bound=SQLModel)

class BaseEnum(ResourceConnectorOnStartUp[RESOURCE]):
    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.example

    def fetch(
        self, limit: int | None = None
    ) -> Iterator[RESOURCE | ResourceWithRelations[RESOURCE] | RecordError]:
        return iter([])


class EnumConnectorApplicationArea(BaseEnum):
    @property
    def resource_class(self) -> type[ApplicationArea]:
        return ApplicationArea


class EnumConnectorEducationalResourceType(BaseEnum):
    @property
    def resource_class(self) -> type[EducationalResourceType]:
        return EducationalResourceType


class EnumConnectorEventMode(BaseEnum):
    @property
    def resource_class(self):
        return EventMode


class EnumConnectorEventStatus(BaseEnum):
    @property
    def resource_class(self):
        return EventStatus


class EnumConnectorLanguage(BaseEnum):
    @property
    def resource_class(self):
        return Language


class EnumConnectorLicense(BaseEnum):
    @property
    def resource_class(self):
        return License


class EnumConnectorOrganisationType(BaseEnum):
    @property
    def resource_class(self):
        return OrganisationType


class EnumConnectorNewsCategory(BaseEnum):
    @property
    def resource_class(self):
        return NewsCategory
