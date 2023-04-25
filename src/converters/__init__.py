from typing import Type  # noqa:F401
from converters.codeArtifact_converter import CodeArtifactConverter  # noqa:F401

from schemas import (
    AIoDDataset,
    AIoDEvent,
    AIoDNews,
    AIoDOrganisation,
    AIoDProject,
    AIoDPublication,
    AIoDEducationalResource,
)
from .abstract_converter import ResourceConverter  # noqa:F401
from .dataset_converter import DatasetConverter
from .news_converter import NewsConverter
from .publication_converter import PublicationConverter
from .educational_resource_converter import EducationalResourceConverter
from .event_converter import EventResourceConverter
from .organisation_converter import OrganisationResourceConverter
from .project_converter import ProjectConverter

dataset_converter_instance = DatasetConverter()
news_converter_instance = NewsConverter()
publication_converter_instance = PublicationConverter()
project_converter_instance = ProjectConverter()
educational_resource_converter_instance = EducationalResourceConverter()
code_artifact_converter_instance = CodeArtifactConverter()
event_converter_instance = EventResourceConverter()
organisation_converter_instance = OrganisationResourceConverter()

converters = {
    AIoDDataset: dataset_converter_instance,
    AIoDEducationalResource: educational_resource_converter_instance,
    AIoDNews: news_converter_instance,
    AIoDPublication: publication_converter_instance,
    AIoDProject: project_converter_instance,
    AIoDEvent: event_converter_instance,
    AIoDOrganisation: organisation_converter_instance,
}  # type: dict[Type, ResourceConverter]
