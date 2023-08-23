from database.model.named_relation import NamedRelation


class Language(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "language"
