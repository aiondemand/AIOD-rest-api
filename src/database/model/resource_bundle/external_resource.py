from database.model.named_relation import NamedRelation


class ExternalResource(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "external_resource"
