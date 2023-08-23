from database.model.named_relation import NamedRelation


class Email(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "email"
