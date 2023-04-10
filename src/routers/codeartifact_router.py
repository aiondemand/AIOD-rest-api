from typing import Type

from converters import codeartifact_converter_instance
from converters.abstract_converter import ResourceConverter
from database.model.codeArtifact import OrmCodeArtifact
from routers.abstract_router import ResourceRouter, AIOD_CLASS, ORM_CLASS
from schemas import AIoDCodeArtifact


class CodeArtifactRouter(ResourceRouter[OrmCodeArtifact, AIoDCodeArtifact]):
    @property
    def resource_name(self) -> str:
        return "codeartifact"

    @property
    def resource_name_plural(self) -> str:
        return "codeartifacts"

    @property
    def aiod_class(self) -> Type[AIOD_CLASS]:
        return AIoDCodeArtifact

    @property
    def orm_class(self) -> Type[ORM_CLASS]:
        return OrmCodeArtifact

    @property
    def converter(self) -> ResourceConverter[AIOD_CLASS, ORM_CLASS]:
        return codeartifact_converter_instance
