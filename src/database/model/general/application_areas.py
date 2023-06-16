from typing import List
from typing import TYPE_CHECKING

from sqlmodel import Relationship
from database.model.event.application_area_link import EventApplicationAreaLink


if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.event.event import Event
from database.model.named_relation import NamedRelation


class ApplicationArea(NamedRelation, table=True):  # type: ignore [call-arg]
    """
    Application area used to describe some item
    """

    __tablename__ = "application_area"

    events: List["Event"] = Relationship(
        back_populates="application_areas", link_model=EventApplicationAreaLink
    )