from database.model.named_relation import NamedRelation


class EventStatus(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "event_status"
