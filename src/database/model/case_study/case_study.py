from database.model.ai_asset.ai_asset import AIAssetBase, AIAsset
from versioning import Version, VersionedResource, VersionedResourceCollection


class CaseStudyBase(AIAssetBase):
    pass


class CaseStudy(CaseStudyBase, AIAsset, table=True):  # type: ignore [call-arg]
    __tablename__ = "case_study"
    __abbreviation__ = "case"
    __plural__ = "case studies"


case_study_versions = VersionedResourceCollection(
    {
        Version.LATEST: VersionedResource(CaseStudy),
        Version.V2: VersionedResource(CaseStudy),
    }
)
