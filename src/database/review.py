import enum
from datetime import datetime, timezone
from typing import Any

import sqlalchemy
from sqlalchemy import Column
from sqlmodel import SQLModel, Field, Relationship, Session

from database.model.field_length import NORMAL, LONG
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses
from routers.helper_functions import get_all_asset_schemas, get_asset_type_by_abbreviation

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


class SubmissionCreateV2(SQLModel):
    """User provided information to submit a review request."""

    comment: str = Field(
        description="Optional. Comment to the reviewer to motivate the submission or provide clarification.",
        max_length=NORMAL,
        default="",
        schema_extra={"example": "'IA' is not a typo, it's for L'intelligence artificielle."},
    )


class SubmissionCreate(SQLModel):
    """User provided information to submit a review request."""

    asset_identifiers: list[str] = Field(
        description="List of identifiers of the assets to submit for review",
        min_length=1,
        schema_extra={"example": ["case_n8DhfFgMYv4beBnVurHa13ZS"]},
    )
    comment: str = Field(
        description="Optional. Comment to the reviewer to motivate the submission or provide clarification.",
        max_length=NORMAL,
        default="",
        schema_extra={"example": "'IA' is not a typo, it's for L'intelligence artificielle."},
    )


class SubmissionBase(SQLModel):
    """A review request, requested by a user to publish an asset/change."""

    identifier: int = Field(primary_key=True, default=None)
    request_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    comment: str = Field(
        description="Optional. Comment to the reviewer to motivate the submission or provide clarification.",
        max_length=NORMAL,
        default="",
        schema_extra={"example": "'IA' is not a typo, it's for L'intelligence artificielle."},
    )


class AssetReview(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "asset_review"
    asset_identifier: str = Field()
    # If the entry corresponding to the thing it reviews is removed,
    # then we also want to permanently remove the review data.
    aiod_entry_identifier: int = Field(
        primary_key=True, nullable=False, foreign_key="aiod_entry.identifier", ondelete="CASCADE"
    )
    review_identifier: int = Field(
        primary_key=True, nullable=False, foreign_key="submission.identifier", ondelete="CASCADE"
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
    _assets: list[AssetReview] = Relationship()

    @property
    def assets(self) -> list[AIoDConcept]:
        # I could not find a way to just use a Relationship directly on account of it needing
        # to be defined on creation but the asset_type is only known at runtime.
        # We still mimic the behavior of a lazy-loaded relationship by fetching the session
        # related to the object, instead of instantiating a new session.
        session = Session.object_session(self)
        available_schemas: list[AIoDConcept] = list(non_abstract_subclasses(AIoDConcept))
        schema_by_name = {schema.__tablename__: schema for schema in available_schemas}

        assets = []
        for identifier in [a.asset_identifier for a in self._assets]:
            prefix, _ = identifier.split("_")
            asset_type = get_asset_type_by_abbreviation()[prefix]
            schema = schema_by_name[asset_type.__tablename__]
            assets.append(session.get(schema, identifier))
        return assets

    @property
    def is_pending(self):
        return len(self.reviews) < REQUIRED_NUMBER_OF_REVIEWS


class SubmissionView(SubmissionBase):
    reviews: list[Review] = Field(default_factory=list)
    # The Asset is of type AIoDConcept, but specifying that here means that SQLModel will
    # only return AIoDConcept fields to the user, instead of all supplied attributes.
    # E.g., a publication's issn is now returned but would not if it was AIoDConcept.
    # Instead we use the configuration below to set the schema annotations.
    assets: Any = Field()

    class Config:
        # This allows us to set the schema generation at runtime, which is necessary since the
        # ResourceRead classes are only defined at runtime (generated dynamically).
        @staticmethod
        def schema_extra(schema: dict[str, Any], _: type["SubmissionView"]) -> None:
            schema["properties"]["assets"] = {
                "type": "array",
                "title": "Assets under review",
                "items": {
                    "title": "Asset",
                    "description": "The type of the object can be derived from its identifier.",
                    "type": "object",
                    "anyOf": get_all_asset_schemas(),
                },
            }
