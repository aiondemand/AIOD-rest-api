from database.model.named_relation import NamedRelation


class ComputationalAssetType(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "computational_asset_type"
