"""
Enum connectors for populating taxonomy and enumeration data in the AIOD database.

This module provides connectors for various enumeration types used throughout
the AIOD platform, such as application areas, resource types, event modes, etc.
"""

import pathlib
from typing import Type, TypeVar

from connectors.example.example_connector import ExampleConnector
from database.model.named_relation import NamedRelation

T = TypeVar('T', bound=NamedRelation)

ENUM_RESOURCE_PATH = pathlib.Path(__file__).parent / "resources" / "enum"


class BaseEnumConnector(ExampleConnector[T]):
    """Base class for enum connectors that load enumeration data from JSON files."""
    
    def __init__(self, enum_filename: str, enum_class: Type[T]):
        json_path = ENUM_RESOURCE_PATH / f"{enum_filename}.json"
        super().__init__(json_path, enum_class)


class EnumConnectorApplicationArea(BaseEnumConnector):
    """Connector for application area enumeration data."""
    
    def __init__(self):
        from database.model.concept.application_area import ApplicationArea
        super().__init__("application_areas", ApplicationArea)


class EnumConnectorEducationalResourceType(BaseEnumConnector):
    """Connector for educational resource type enumeration data."""
    
    def __init__(self):
        from database.model.concept.educational_resource_type import EducationalResourceType
        super().__init__("educational_resource_types", EducationalResourceType)


class EnumConnectorEventMode(BaseEnumConnector):
    """Connector for event mode enumeration data."""
    
    def __init__(self):
        from database.model.concept.event_mode import EventMode
        super().__init__("event_modes", EventMode)


class EnumConnectorEventStatus(BaseEnumConnector):
    """Connector for event status enumeration data."""
    
    def __init__(self):
        from database.model.concept.event_status import EventStatus
        super().__init__("event_statuses", EventStatus)


class EnumConnectorLanguage(BaseEnumConnector):
    """Connector for language enumeration data."""
    
    def __init__(self):
        from database.model.concept.language import Language
        super().__init__("languages", Language)


class EnumConnectorLicense(BaseEnumConnector):
    """Connector for license enumeration data."""
    
    def __init__(self):
        from database.model.concept.license import License
        super().__init__("licenses", License)


class EnumConnectorOrganisationType(BaseEnumConnector):
    """Connector for organisation type enumeration data."""
    
    def __init__(self):
        from database.model.concept.organisation_type import OrganisationType
        super().__init__("organisation_types", OrganisationType)


class EnumConnectorNewsCategory(BaseEnumConnector):
    """Connector for news category enumeration data."""
    
    def __init__(self):
        from database.model.concept.news_category import NewsCategory
        super().__init__("news_categories", NewsCategory)
