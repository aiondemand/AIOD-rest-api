from database.model.named_relation import Taxonomy


class PublicationType(Taxonomy, table=True):  # type: ignore [call-arg]
    __tablename__ = "publication_type"
