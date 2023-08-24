from database.model.event.event import Event
from routers.resource_router import ResourceRouter


class EventRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "event"

    @property
    def resource_name_plural(self) -> str:
        return "events"

    @property
    def resource_class(self) -> type[Event]:
        return Event
