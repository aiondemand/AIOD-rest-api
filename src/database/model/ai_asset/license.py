from database.model.named_relation import NamedRelation


class License(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "license"
