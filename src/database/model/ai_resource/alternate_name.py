from database.model.named_relation import NamedRelation


class AlternateName(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "alternate_name"
