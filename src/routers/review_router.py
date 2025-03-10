import enum
from http import HTTPStatus
from typing import Sequence, Literal, cast

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select, Session
from starlette import status

from authentication import KeycloakUser, get_user_or_raise
from database.authorization import register_user, user_can_administer
from database.session import DbSession, get_session
from database.review import (
    Submission,
    Review,
    SubmissionView,
    SubmissionBase,
    ReviewCreate,
    Decision,
)
from database.model.concept.aiod_entry import EntryStatus, AIoDEntryORM


def create(url_prefix: str) -> APIRouter:
    router = APIRouter()
    version = "v1"

    router.get(
        f"{url_prefix}/submissions/{version}/",
        tags=["Reviewing"],
        description="List all assets submitted for review.",
        response_model=Sequence[SubmissionBase],
    )(list_submissions)

    router.get(
        f"{url_prefix}/submissions/{version}/{{identifier}}",
        tags=["Reviewing"],
        description="Retrieve a specific submission.",
        response_model=SubmissionView,
    )(get_submission)

    router.post(
        f"{url_prefix}/reviews/{version}",
        tags=["Reviewing"],
        description="Review an asset.",
        response_model=Review,
    )(_review_resource)

    # Add MiddleWare which requires authentication as reviewer role
    return router


class ListMode(enum.StrEnum):
    OLDEST = enum.auto()
    NEWEST = enum.auto()
    ALL = enum.auto()
    PENDING = enum.auto()
    COMPLETED = enum.auto()


def _get_single_submission(
    *, which: Literal[ListMode.NEWEST, ListMode.OLDEST]
) -> Submission | None:
    with DbSession() as session:
        has_review = select(1).where(Submission.identifier == Review.submission_identifier).exists()
        order = Submission.request_date
        if which == ListMode.NEWEST:
            order = Submission.request_date.desc()  # type: ignore[attr-defined]
        query = select(Submission).order_by(order).where(~has_review)
        return session.scalars(query).first()


def _get_submissions_by_state(
    *, which: Literal[ListMode.COMPLETED, ListMode.PENDING]
) -> Sequence[Submission]:
    with DbSession() as session:
        has_review = select(1).where(Submission.identifier == Review.submission_identifier).exists()
        if which == ListMode.PENDING:
            submissions = select(Submission).where(~has_review)
        if which == ListMode.COMPLETED:
            submissions = select(Submission).where(has_review)
        return session.scalars(submissions).all()


def list_submissions(mode: ListMode = ListMode.NEWEST) -> Sequence[Submission]:
    # mypy does not do type narrowing properly: https://github.com/python/mypy/issues/12535
    if mode in [ListMode.NEWEST, ListMode.OLDEST]:
        submission = _get_single_submission(which=mode)  # type: ignore[arg-type]
        return [submission] if submission else []
    if mode in [ListMode.PENDING, ListMode.COMPLETED]:
        return _get_submissions_by_state(which=mode)  # type: ignore[arg-type]
    raise ValueError(f"`mode` should be one of {ListMode!r} but is {mode!r}.")


def get_submission(identifier: int, session=Depends(get_session)) -> Submission:
    query = select(Submission).where(Submission.identifier == identifier)
    submission = session.scalars(query).first()
    if submission:
        return submission
    raise HTTPException(
        status_code=HTTPStatus.NOT_FOUND,
        detail=f"No submission with identifier {identifier} found.",
    )


def _review_resource(
    review: ReviewCreate,
    user: KeycloakUser = Depends(get_user_or_raise),
    session: Session = Depends(get_session),
):
    if "reviewer" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must have reviewing privileges to use this endpoint.",
        )

    submission = session.get(Submission, review.submission_identifier)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No review with identifier {review.submission_identifier} found.",
        )
    if not submission.is_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review is no longer pending, no new decision may be made.",
        )
    register_user(user, session)

    aiod_entry = cast(AIoDEntryORM, session.get(AIoDEntryORM, submission.aiod_entry_identifier))
    if user_can_administer(user, aiod_entry):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to review your own assets.",
        )

    if review.decision == Decision.ACCEPTED:
        new_status = EntryStatus.PUBLISHED
    else:
        new_status = EntryStatus.DRAFT
    aiod_entry.status = new_status

    review = Review(
        reviewer_identifier=user._subject_identifier,
        comment=review.comment,
        decision=review.decision,
        submission_identifier=submission.identifier,
    )
    session.add(review)
    session.commit()
    return review
