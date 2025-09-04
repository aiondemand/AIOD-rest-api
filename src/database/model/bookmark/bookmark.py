from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String


class Bookmark(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "bookmark"
    __plural__ = "bookmarks"
    user_identifier: str = Field(
        foreign_key="user.subject_identifier",
        nullable=False,
        ondelete="CASCADE",
        primary_key=True,
        description="The sub-identifier of the user who created the bookmark.",
    )
    resource_identifier: str = Field(
        primary_key=True, description="The identifier of the resource being bookmarked."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="The time when the bookmark was created."
    )
