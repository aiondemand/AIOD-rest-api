from database.model.named_relation import NamedRelation


class ScientificDomain(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "scientific_domain"
