from database.model.case_study.case_study import CaseStudy
from routers.resource_router import ResourceRouter


class CaseStudyRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "case_study"

    @property
    def resource_name_plural(self) -> str:
        return "case_studies"

    @property
    def resource_class(self) -> type[CaseStudy]:
        return CaseStudy
