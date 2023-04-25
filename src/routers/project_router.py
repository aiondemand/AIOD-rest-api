from typing import Type

from converters import project_converter_instance
from converters.abstract_converter import ResourceConverter
from database.model.project import OrmProject
from routers.abstract_router import ResourceRouter, AIOD_CLASS, ORM_CLASS
from schemas import AIoDProject


class ProjectRouter(ResourceRouter[OrmProject, AIoDProject]):
    @property
    def version(self) -> int:
        return 0

    @property
    def resource_name(self) -> str:
        return "project"

    @property
    def resource_name_plural(self) -> str:
        return "projects"

    @property
    def aiod_class(self) -> Type[AIOD_CLASS]:
        return AIoDProject

    @property
    def orm_class(self) -> Type[ORM_CLASS]:
        return OrmProject

    @property
    def converter(self) -> ResourceConverter[AIOD_CLASS, ORM_CLASS]:
        return project_converter_instance
