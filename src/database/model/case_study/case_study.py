from database.model.ai_asset.ai_asset import AIAssetBase, AIAsset


class CaseStudyBase(AIAssetBase):
    pass


class CaseStudy(CaseStudyBase, AIAsset, table=True):  # type: ignore [call-arg]
    __tablename__ = "case_study"
