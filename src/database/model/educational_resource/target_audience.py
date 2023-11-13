from database.model.named_relation import NamedRelation


class TargetAudience(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "edu_target_audience"
