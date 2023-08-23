from database.model.platform.platform import Platform
from routers.resource_router import ResourceRouter


class PlatformRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "platform"

    @property
    def resource_name_plural(self) -> str:
        return "platforms"

    @property
    def resource_class(self) -> type[Platform]:
        return Platform
