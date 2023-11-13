import pathlib

from connectors.example.enum_fill_connector import EnumConnector
from database.model.agent.language import Language
from database.model.agent.organisation_type import OrganisationType
from database.model.ai_asset.license import License
from database.model.ai_resource.application_area import ApplicationArea
from database.model.concept.status import Status
from database.model.educational_resource.educational_resource_type import EducationalResourceType
from database.model.event.event_mode import EventMode
from database.model.event.event_status import EventStatus
from database.model.news.news_category import NewsCategory

ENUM_PATH = pathlib.Path(__file__).parent.parent / "example" / "resources" / "enum"


class EnumConnectorApplicationArea(EnumConnector[ApplicationArea]):
    def __init__(self):
        json_path = ENUM_PATH / "application_areas.json"
        super().__init__(json_path, ApplicationArea)


class EnumConnectorEducationalResourceType(EnumConnector[EducationalResourceType]):
    def __init__(self):
        json_path = ENUM_PATH / "educational_resource_types.json"
        super().__init__(json_path, EducationalResourceType)


class EnumConnectorEventMode(EnumConnector[EventMode]):
    def __init__(self):
        json_path = ENUM_PATH / "event_modes.json"
        super().__init__(json_path, EventMode)


class EnumConnectorEventStatus(EnumConnector[EventStatus]):
    def __init__(self):
        json_path = ENUM_PATH / "event_status.json"
        super().__init__(json_path, EventStatus)


class EnumConnectorLanguage(EnumConnector[Language]):
    def __init__(self):
        json_path = ENUM_PATH / "languages.json"
        super().__init__(json_path, Language)


class EnumConnectorLicense(EnumConnector[License]):
    def __init__(self):
        json_path = ENUM_PATH / "licenses.json"
        super().__init__(json_path, License)


class EnumConnectorOrganisationType(EnumConnector[OrganisationType]):
    def __init__(self):
        json_path = ENUM_PATH / "organisation_types.json"
        super().__init__(json_path, OrganisationType)


class EnumConnectorNewsCategory(EnumConnector[NewsCategory]):
    def __init__(self):
        json_path = ENUM_PATH / "news_categories.json"
        super().__init__(json_path, NewsCategory)


class EnumConnectorStatus(EnumConnector[Status]):
    def __init__(self):
        json_path = ENUM_PATH / "status.json"
        super().__init__(json_path, Status)
