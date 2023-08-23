from database.model.named_relation import NamedRelation


class ResearchArea(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "research_area"
