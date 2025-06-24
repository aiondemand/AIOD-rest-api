from database.model.named_relation import Taxonomy


class License(Taxonomy, table=True):  # type: ignore [call-arg]
    __tablename__ = "license"
