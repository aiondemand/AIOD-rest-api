from database.model.case_study.case_study import CaseStudy, case_study_versions
from routers.resource_ai_asset_router import ResourceAIAssetRouter


class CaseStudyRouter(ResourceAIAssetRouter):
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


case_study_routers = {
    version: CaseStudyRouter(versioned_resource)
    for version, versioned_resource in case_study_versions.items()
}
