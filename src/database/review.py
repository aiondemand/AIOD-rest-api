import enum
from datetime import datetime, timezone

import sqlalchemy
from sqlalchemy import Column
from sqlmodel import SQLModel, Field, Relationship

from database.model.field_length import NORMAL, LONG

REQUIRED_NUMBER_OF_REVIEWS = 1


class Decision(enum.StrEnum):
    ACCEPTED = enum.auto()
    REJECTED = enum.auto()
    RETRACTED = enum.auto()


class ReviewBase(SQLModel):
    """A review (which may be pending), requested by a user to publish an asset/change."""

    comment: str = Field(
        description="Motivation for the decision.",
        max_length=LONG,
        default="",
        schema_extra={"example": "The organization's contact information is invalid."},
    )
    decision: Decision = Field(
        description="The decision made by the reviewer.",
        sa_column=Column(sqlalchemy.Enum(Decision)),
    )
    submission_identifier: int = Field(
        description="The identifier of the submission (review request)."
    )


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "review"

    identifier: int = Field(primary_key=True, default=None)
    decision_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    reviewer_identifier: str = Field(foreign_key="user.subject_identifier", exclude=True)
    submission_identifier: int = Field(foreign_key="submission.identifier")
    submission: "Submission" = Relationship(back_populates="reviews")


class SubmissionCreate(SQLModel):
    """User provided information to submit a review request."""

    comment: str = Field(
        description="Optional. Comment to the reviewer to motivate the submission or provide clarification.",
        max_length=NORMAL,
        default="",
        schema_extra={"example": "'IA' is not a typo, it's for L'intelligence artificielle."},
    )


class SubmissionBase(SubmissionCreate):
    """A review request, requested by a user to publish an asset/change."""

    identifier: int = Field(primary_key=True, default=None)
    request_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # If the entry corresponding to the thing it reviews is removed,
    # then we also want to permanently remove the review data.
    aiod_entry_identifier: int = Field(foreign_key="aiod_entry.identifier", ondelete="CASCADE")
    asset_type: str = Field(
        description="The name of the table of the resource. E.g. 'dataset' or 'person'"
    )


class Submission(SubmissionBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "submission"
    # We do not want the review to be deleted when the original requestee is deleted,
    # there could be e.g., shared ownership in which case the review data should be preserved.
    requestee_identifier: str | None = Field(
        foreign_key="user.subject_identifier",
        ondelete="SET NULL",
    )

    reviews: list[Review] = Relationship(back_populates="submission")

    @property
    def is_pending(self):
        return len(self.reviews) < REQUIRED_NUMBER_OF_REVIEWS


class SubmissionWithReviews(SubmissionBase):
    reviews: list[Review] = Field(default_factory=list)
