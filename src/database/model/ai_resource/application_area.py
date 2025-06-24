from database.model.named_relation import NamedRelation


class ApplicationArea(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "application_area"
