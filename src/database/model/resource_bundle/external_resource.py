from database.model.named_relation import NamedRelation


class ExternalResource(NamedRelation, table=True):  # type: ignore [call-arg]
    """
    Stores external resources (URLs).
    """

    __tablename__ = "external_resource"
