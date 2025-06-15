from database.model.named_relation import Taxonomy


class ResearchArea(Taxonomy, table=True):  # type: ignore [call-arg]
    __tablename__ = "research_area"
