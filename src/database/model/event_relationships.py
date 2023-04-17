import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)

from sqlalchemy import ForeignKey, Table, Column

from database.model.base import Base

event_business_category_relationship = Table(
    "event_business_category",
    Base.metadata,
    Column(
        "event_id",
        ForeignKey("events.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "business_category_id",
        ForeignKey("business_categories.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
)

event_research_area_relationship = Table(
    "event_research_area",
    Base.metadata,
    Column(
        "event_id",
        ForeignKey("events.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "research_area_id",
        ForeignKey("research_areas.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
)

event_application_area_relationship = Table(
    "event_application_area",
    Base.metadata,
    Column(
        "event_id",
        ForeignKey("events.identifier", ondelete="CASCADE", onupdate="RESTRICT"),
        primary_key=True,
    ),
    Column(
        "application_area_id",
        ForeignKey("application_areas.identifier", ondelete="CASCADE", onupdate="RESTRICT"),
        primary_key=True,
    ),
)

event_event_relationship = Table(
    "event_event",
    Base.metadata,
    Column("parent_id", ForeignKey("events.identifier")),
    Column("child_id", ForeignKey("events.identifier")),
)

event_relevant_ai_resource_relationship = Table(
    "event_relevant_ai_resource",
    Base.metadata,
    Column(
        "event_id",
        ForeignKey("events.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "ai_resource_id",
        ForeignKey("ai_resources.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
)


event_used_ai_resource_relationship = Table(
    "event_used_ai_resource",
    Base.metadata,
    Column(
        "event_id",
        ForeignKey("events.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "ai_resource_id",
        ForeignKey("ai_resources.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
)
