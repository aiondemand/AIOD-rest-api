from database.model.named_relation import NamedRelation


class EventMode(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "event_mode"
