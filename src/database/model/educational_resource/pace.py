from database.model.named_relation import NamedRelation


class Pace(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "edu_pace"
