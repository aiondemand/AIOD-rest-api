from database.model.educational_resource.educational_resource import EducationalResource

from routers.resource_router import ResourceRouter
from versioning import Version


class EducationalResourceRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "educational_resource"

    @property
    def resource_name_plural(self) -> str:
        return "educational_resources"

    @property
    def resource_class(self) -> type[EducationalResource]:
        return EducationalResource


educational_resource_routers = {
    Version.V2: EducationalResourceRouter(),
    Version.LATEST: EducationalResourceRouter(),
}
