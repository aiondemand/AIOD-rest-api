from database.model.event.event import Event, event_versions
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


event_routers = {
    version: EventRouter(versioned_resource)
    for version, versioned_resource in event_versions.items()
}
