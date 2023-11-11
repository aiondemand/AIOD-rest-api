from database.model.project.project import Project
from routers.search_router import SearchRouter


class SearchRouterProjects(SearchRouter[Project]):
    @property
    def es_index(self) -> str:
        return "project"

    @property
    def resource_name_plural(self) -> str:
        return "projects"

    @property
    def resource_class(self):
        return Project
    
    @property
    def match_fields(self):
        return set(['name', 'description', 'coordinator_name'])
