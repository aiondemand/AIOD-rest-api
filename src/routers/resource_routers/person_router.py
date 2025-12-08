from database.model.agent.person import Person, person_versions
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


person_routers = {
    version: PersonRouter(versioned_resource)
    for version, versioned_resource in person_versions.items()
}
