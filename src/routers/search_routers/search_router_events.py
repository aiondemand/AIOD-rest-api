from database.model.event.event import Event
from routers.search_router import SearchRouter


class SearchRouterEvents(SearchRouter[Event]):
    @property
    def es_index(self) -> str:
        return "event"

    @property
    def resource_name_plural(self) -> str:
        return "events"

    @property
    def resource_class(self):
        return Event
