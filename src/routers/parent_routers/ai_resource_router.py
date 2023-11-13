from typing import Type

from database.model.ai_resource.resource import AbstractAIResource
from database.model.ai_resource.resource_table import AIResourceORM
from routers.parent_router import ParentRouter


class AIResourceRouter(ParentRouter):
    @property
    def resource_name(self) -> str:
        return "ai_resource"

    @property
    def resource_name_plural(self) -> str:
        return "ai_resources"

    @property
    def parent_class(self) -> Type[AbstractAIResource]:
        return AbstractAIResource

    @property
    def parent_class_table(self) -> Type[AIResourceORM]:
        return AIResourceORM
