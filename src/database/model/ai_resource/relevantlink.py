from database.model.named_relation import NamedRelation


class RelevantLink(NamedRelation, table=True):  # type: ignore [call-arg]
    """An address of a resource on the web"""

    __tablename__ = "relevant_link"
