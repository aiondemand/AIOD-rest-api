from database.model.agent.organisational_network import OrganisationalNetwork, organisational_network_versions
from routers.resource_router import ResourceRouter


class OrganisationalNetworkRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "organisational_network"

    @property
    def resource_name_plural(self) -> str:
        return "organisational_networks"

    @property
    def resource_class(self) -> type[OrganisationalNetwork]:
        return OrganisationalNetwork

organisational_network_routers = {
    version: OrganisationalNetworkRouter(versioned_resource)
    for version, versioned_resource in organisational_network_versions.items()
}
