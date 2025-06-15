from database.model.named_relation import Taxonomy


class ApplicationArea(Taxonomy, table=True):  # type: ignore [call-arg]
    __tablename__ = "application_area"
