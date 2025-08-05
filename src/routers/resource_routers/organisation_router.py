from database.model.agent.organisation import Organisation, organisation_versions
from routers.resource_router import ResourceRouter


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
    version: OrganisationRouter(versioned_resource)
    for version, versioned_resource in organisation_versions.items()
}
