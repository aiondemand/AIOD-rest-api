from typing import Type

from converters import news_converter_instance
from converters.abstract_converter import ResourceConverter
from database.model.news import OrmNews
from routers.abstract_router import ResourceRouter, AIOD_CLASS, ORM_CLASS
from schemas import AIoDNews


class NewsRouter(ResourceRouter[OrmNews, AIoDNews]):
    @property
    def version(self) -> int:
        return 0

    @property
    def resource_name(self) -> str:
        return "news"

    @property
    def resource_name_plural(self) -> str:
        return "news"

    @property
    def aiod_class(self) -> Type[AIOD_CLASS]:
        return AIoDNews

    @property
    def orm_class(self) -> Type[ORM_CLASS]:
        return OrmNews

    @property
    def converter(self) -> ResourceConverter[AIOD_CLASS, ORM_CLASS]:
        return news_converter_instance
