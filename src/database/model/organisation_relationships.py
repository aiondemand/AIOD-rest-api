import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)

from sqlalchemy import ForeignKey, Table, Column

from database.model.base import Base

organisation_business_category_relationship = Table(
    "organisation_business_category",
    Base.metadata,
    Column(
        "organisation_id",
        ForeignKey("organisations.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "business_category_id",
        ForeignKey("business_categories.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
)

organisation_technical_category_relationship = Table(
    "organisation_technical_category",
    Base.metadata,
    Column(
        "organisation_id",
        ForeignKey("organisations.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "technical_category_id",
        ForeignKey("technical_categories.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
)


organisation_member_agent_relationship = Table(
    "organisation_member_agent",
    Base.metadata,
    Column(
        "organisation_id",
        ForeignKey("organisations.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "agent_id",
        ForeignKey("agents.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
)


organisation_department_agent_relationship = Table(
    "organisation_department_agent",
    Base.metadata,
    Column(
        "organisation_id",
        ForeignKey("organisations.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "agent_id",
        ForeignKey("agents.identifier", ondelete="CASCADE"),
        primary_key=True,
    ),
)
