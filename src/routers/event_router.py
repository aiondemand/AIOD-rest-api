from typing import Type

from converters import event_converter_instance
from converters.abstract_converter import ResourceConverter
from database.model.event import OrmEvent
from routers.abstract_router import ResourceRouter, AIOD_CLASS, ORM_CLASS
from schemas import AIoDEvent


class EventRouter(ResourceRouter[OrmEvent, AIoDEvent]):
    @property
    def version(self) -> int:
        return 0

    @property
    def resource_name(self) -> str:
        return "event"

    @property
    def resource_name_plural(self) -> str:
        return "events"

    @property
    def aiod_class(self) -> Type[AIOD_CLASS]:
        return AIoDEvent

    @property
    def orm_class(self) -> Type[ORM_CLASS]:
        return OrmEvent

    @property
    def converter(self) -> ResourceConverter[AIOD_CLASS, ORM_CLASS]:
        return event_converter_instance
