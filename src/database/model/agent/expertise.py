from database.model.named_relation import NamedRelation


class Expertise(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "expertise"
