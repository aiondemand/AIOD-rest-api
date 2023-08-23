from database.model.named_relation import NamedRelation


class PublicationType(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "publication_type"
