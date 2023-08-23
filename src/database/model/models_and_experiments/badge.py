from database.model.named_relation import NamedRelation


class Badge(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "badge"
