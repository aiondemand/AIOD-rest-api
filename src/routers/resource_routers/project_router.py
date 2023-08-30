from database.model.project.project import Project
from routers.resource_router import ResourceRouter


class ProjectRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "project"

    @property
    def resource_name_plural(self) -> str:
        return "projects"

    @property
    def resource_class(self) -> type[Project]:
        return Project
