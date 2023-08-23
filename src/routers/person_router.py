from database.model.agent.person import Person
from routers.resource_router import ResourceRouter


class PersonRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "person"

    @property
    def resource_name_plural(self) -> str:
        return "persons"

    @property
    def resource_class(self) -> type[Person]:
        return Person
