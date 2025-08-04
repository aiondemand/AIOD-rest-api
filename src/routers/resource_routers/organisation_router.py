from database.model.agent.organisation import Organisation
from routers.resource_router import ResourceRouter
from versioning import Version


class OrganisationRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "organisation"

    @property
    def resource_name_plural(self) -> str:
        return "organisations"

    @property
    def resource_class(self) -> type[Organisation]:
        return Organisation


organisation_routers = {
    Version.V2: OrganisationRouter(),
    Version.LATEST: OrganisationRouter(),
}
