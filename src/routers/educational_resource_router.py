from typing import Type

from converters import educational_resource_converter_instance
from converters.abstract_converter import ResourceConverter
from database.model.educational_resource import OrmEducationalResource
from routers.abstract_router import ResourceRouter, AIOD_CLASS, ORM_CLASS
from schemas import AIoDEducationalResource


class EducationalResourceRouter(ResourceRouter[OrmEducationalResource, AIoDEducationalResource]):
    @property
    def version(self) -> int:
        return 0

    @property
    def resource_name(self) -> str:
        return "educational_resources"

    @property
    def resource_name_plural(self) -> str:
        return "educational_resources"

    @property
    def aiod_class(self) -> Type[AIOD_CLASS]:
        return AIoDEducationalResource

    @property
    def orm_class(self) -> Type[ORM_CLASS]:
        return OrmEducationalResource

    @property
    def converter(self) -> ResourceConverter[AIOD_CLASS, ORM_CLASS]:
        return educational_resource_converter_instance
