from sqlalchemy import Table, Column, ForeignKey

from database.model.base import Base

project_keyword_relationship = Table(
    "projects_keyword",
    Base.metadata,
    Column("keyword_id", ForeignKey("keywords.identifier")),
    Column("project_id", ForeignKey("projects.identifier")),
)
