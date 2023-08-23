from database.model.named_relation import NamedRelation


class Telephone(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "telephone"
