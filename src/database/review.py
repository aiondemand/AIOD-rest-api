import enum
from datetime import datetime, timezone

import sqlalchemy
from pydantic.main import BaseModel
from sqlalchemy import Column
from sqlmodel import SQLModel, Field, Relationship


REQUIRED_NUMBER_OF_REVIEWS = 1


class Decision(enum.StrEnum):
    ACCEPTED = enum.auto()
    REJECTED = enum.auto()
    RETRACTED = enum.auto()


class Review(SQLModel, table=True):  # type: ignore [call-arg]
    """A review (which may be pending), requested by a user to publish an asset/change."""

    __tablename__ = "review"

    identifier: int = Field(primary_key=True, default=None)
    decision_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Not sure if size should be limited, especially if we want to use this for structured data.
    comment: str | None = Field()
    decision: Decision = Field(sa_column=Column(sqlalchemy.Enum(Decision)))

    reviewer_identifier: str = Field(
        foreign_key="user.subject_identifier",
        exclude=True,
    )
    submission_identifier: int = Field(
        foreign_key="submission.identifier",
    )
    submission: "Submission" = Relationship(back_populates="reviews")


class ReviewCreate(BaseModel):
    comment: str | None = Field(description="Motivation for the decision.")
    decision: Decision = Field(description="The decision made by the reviewer.")
    submission_identifier: int = Field(
        description="The identifier of the submission (review request)."
    )


class Submission(SQLModel, table=True):  # type: ignore [call-arg]
    """A review request, requested by a user to publish an asset/change."""

    __tablename__ = "submission"

    identifier: int = Field(primary_key=True, default=None)
    request_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # We do not want the review to be deleted when the original requestee is deleted,
    # there could be e.g., shared ownership in which case the review data should be preserved.
    requestee_identifier: str | None = Field(
        foreign_key="user.subject_identifier",
        ondelete="SET NULL",
        exclude=True,
    )

    # On the other hand, if the entry corresponding to the thing it reviews is removed,
    # then we also want to permanently remove the review data.
    aiod_entry_identifier: int = Field(
        foreign_key="aiod_entry.identifier", ondelete="CASCADE"
    )

    reviews: list[Review] = Relationship(back_populates="submission")

    @property
    def is_pending(self):
        return len(self.reviews) < REQUIRED_NUMBER_OF_REVIEWS
