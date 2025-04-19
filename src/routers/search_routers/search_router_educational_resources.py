from database.model.educational_resource.educational_resource import EducationalResource
from routers.search_router import SearchRouter


class SearchRouterEducationalResources(SearchRouter[EducationalResource]):
    @property
    def es_index(self) -> str:
        return "educational_resource"

    @property
    def resource_name_plural(self) -> str:
        return "educational_resources"

    @property
    def key_translations(self) -> dict[str, str]:
        return {
            "edu_access_mode": "access_mode",
            "edu_educational_level": "educational_level",
            "edu_prerequisite": "prerequisite",
            "edu_target_audience": "target_audience",
        }

    @property
    def resource_class(self):
        return EducationalResource

    @property
    def linked_fields(self) -> set[str]:
        return {
            "alternate_name",
            "application_area",
            "industrial_sector",
            "research_area",
            "scientific_domain",
            "edu_access_mode",
            "edu_educational_level",
            "edu_prerequisite",
            "edu_target_audience",
        }
