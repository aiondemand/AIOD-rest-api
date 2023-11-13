from database.model.named_relation import NamedRelation


class AccessMode(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "edu_access_mode"
