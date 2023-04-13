from typing import Type  # noqa:F401
from converters.codeArtifact_converter import CodeArtifactConverter  # noqa:F401

from schemas import AIoDDataset, AIoDNews, AIoDPublication, AIoDEducationalResource
from .abstract_converter import ResourceConverter  # noqa:F401
from .dataset_converter import DatasetConverter
from .news_converter import NewsConverter
from .publication_converter import PublicationConverter
from .educational_resource_converter import EducationalResourceConverter

dataset_converter_instance = DatasetConverter()
news_converter_instance = NewsConverter()
publication_converter_instance = PublicationConverter()
educational_resource_converter_instance = EducationalResourceConverter()
code_artifact_converter_instance = CodeArtifactConverter()


converters = {
    AIoDDataset: dataset_converter_instance,
    AIoDEducationalResource: educational_resource_converter_instance,
    AIoDNews: news_converter_instance,
    AIoDPublication: publication_converter_instance,
}  # type: dict[Type, ResourceConverter]
