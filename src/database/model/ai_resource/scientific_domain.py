from database.model.named_relation import Taxonomy


class ScientificDomain(Taxonomy, table=True):  # type: ignore [call-arg]
    __tablename__ = "scientific_domain"
