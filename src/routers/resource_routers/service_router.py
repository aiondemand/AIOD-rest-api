from database.model.service.service import Service, service_versions
from routers.resource_router import ResourceRouter


class ServiceRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "service"

    @property
    def resource_name_plural(self) -> str:
        return "services"

    @property
    def resource_class(self) -> type[Service]:
        return Service


service_routers = {
    version: ServiceRouter(versioned_resource)
    for version, versioned_resource in service_versions.items()
}
