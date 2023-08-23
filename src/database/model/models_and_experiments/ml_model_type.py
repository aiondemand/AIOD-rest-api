from database.model.named_relation import NamedRelation


class MLModelType(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "ml_model_type"
