from database.model.named_relation import NamedRelation

class ExternalResource(NamedRelation, table=True):
    """
    Stores external resources (URLs).
    """
    __tablename__ = "external_resource"