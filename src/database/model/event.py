import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)
from sqlite3 import Date

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.model.base import Base
from database.model.event_relationships import (
    event_business_category_relationship,
    event_research_area_relationship,
    event_application_area_relationship,
    event_event_relationship,
    event_relevant_ai_resource_relationship,
    event_used_ai_resource_relationship,
)
from database.model.general import OrmBusinessCategory
from database.model.ai_resource import OrmAIResource
from database.model.resource import OrmResource


from database.model.unique_model import UniqueMixin


class OrmResearchArea(UniqueMixin, Base):
    __tablename__ = "research_areas"

    @classmethod
    def _unique_hash(cls, name):
        return name

    @classmethod
    def _unique_filter(cls, query, name):
        return query.filter(cls.name == name)

    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)
    events: Mapped[list["OrmEvent"]] = relationship(
        default_factory=list,
        back_populates="research_areas",
        secondary=event_research_area_relationship,
    )


class OrmApplicationArea(UniqueMixin, Base):
    __tablename__ = "application_areas"

    @classmethod
    def _unique_hash(cls, name):
        return name

    @classmethod
    def _unique_filter(cls, query, name):
        return query.filter(cls.name == name)

    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)

    events: Mapped[list["OrmEvent"]] = relationship(
        default_factory=list,
        back_populates="application_areas",
        secondary=event_application_area_relationship,
    )


class OrmEvent(OrmResource):
    """Any event resource"""

    __tablename__ = "events"

    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)

    # required fields
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String(5000), nullable=False)
    registration_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)

    # optional fields
    start_date: Mapped[Date] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
    end_date: Mapped[Date] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
    duration: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(500), nullable=True)
    attendance_mode: Mapped[str] = mapped_column(String(500), nullable=True)
    type: Mapped[str] = mapped_column(String(500), nullable=True)

    # relationships

    business_categories: Mapped[list["OrmBusinessCategory"]] = relationship(
        secondary=event_business_category_relationship,
        back_populates="events",
        passive_deletes=True,
        default_factory=list,
    )
    research_areas: Mapped[list["OrmResearchArea"]] = relationship(
        secondary=event_research_area_relationship,
        back_populates="events",
        passive_deletes=True,
        default_factory=list,
    )
    application_areas: Mapped[list["OrmApplicationArea"]] = relationship(
        secondary=event_application_area_relationship,
        back_populates="events",
        passive_deletes=True,
        default_factory=list,
    )

    relevant_resources: Mapped[list["OrmAIResource"]] = relationship(
        secondary=event_relevant_ai_resource_relationship,
        backref="relevant_resources",
        passive_deletes=True,
        default_factory=list,
    )

    used_resources: Mapped[list["OrmAIResource"]] = relationship(
        secondary=event_used_ai_resource_relationship,
        backref="used_resources",
        passive_deletes=True,
        default_factory=list,
    )

    sub_events: Mapped[list["OrmEvent"]] = relationship(
        default_factory=list,
        back_populates="sub_events",
        primaryjoin=event_event_relationship.c.parent_id == identifier,
        secondary=event_event_relationship,
        secondaryjoin=event_event_relationship.c.child_id == identifier,
    )
    super_events: Mapped[list["OrmEvent"]] = relationship(
        default_factory=list,
        back_populates="super_events",
        primaryjoin=event_event_relationship.c.parent_id == identifier,
        secondary=event_event_relationship,
        secondaryjoin=event_event_relationship.c.child_id == identifier,
    )
