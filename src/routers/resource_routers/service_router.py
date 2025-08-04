from database.model.service.service import Service
from routers.resource_router import ResourceRouter
from versioning import Version


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
    Version.V2: ServiceRouter(),
    Version.LATEST: ServiceRouter(),
}
