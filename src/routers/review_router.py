import enum
from http import HTTPStatus
from typing import Sequence, Literal, cast

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select, Session
from starlette import status

from authentication import KeycloakUser, get_user_or_raise
from database.authorization import register_user, user_can_administer, user_can_write
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
from versioning import Version


def create(url_prefix: str, version: Version) -> APIRouter:
    router = APIRouter()

    router.post(
        "/submissions/retract/{submission_identifier}",
        tags=["Reviewing"],
        description="Retract an asset under review, setting its status to 'draft'.",
    )(retract_submission)

    router.get(
        "/submissions/{identifier}",
        tags=["Reviewing"],
        description="Retrieve a specific submission.",
        response_model=SubmissionView,
    )(get_submission)

    router.get(
        "/submissions",
        tags=["Reviewing"],
        description="List all assets submitted for review.",
        response_model=Sequence[SubmissionBase],
    )(list_submissions)

    router.post(
        "/reviews",
        tags=["Reviewing"],
        description="Review an asset.",
        response_model=Review,
    )(_review_resource)
    return router


class ListMode(enum.StrEnum):
    OLDEST = enum.auto()
    NEWEST = enum.auto()
    ALL = enum.auto()
    PENDING = enum.auto()
    COMPLETED = enum.auto()


def _get_single_submission(
    *,
    which: Literal[ListMode.NEWEST, ListMode.OLDEST],
    from_requestee: str | None = None,
) -> Submission | None:
    with DbSession() as session:
        has_review = select(1).where(Submission.identifier == Review.submission_identifier).exists()
        submissions = select(Submission).where(~has_review)
        if which == ListMode.NEWEST:
            submissions = submissions.order_by(Submission.request_date.desc())  # type: ignore[attr-defined]
        if from_requestee is not None:
            submissions = submissions.where(Submission.requestee_identifier == from_requestee)

        return session.scalars(submissions).first()


def _get_submissions_by_state(
    *,
    which: Literal[ListMode.COMPLETED, ListMode.PENDING, ListMode.ALL],
    from_requestee: str | None = None,
) -> Sequence[Submission]:
    with DbSession() as session:
        has_review = select(1).where(Submission.identifier == Review.submission_identifier).exists()
        submissions = select(Submission)
        if which == ListMode.PENDING:
            submissions = submissions.where(~has_review)
        if which == ListMode.COMPLETED:
            submissions = submissions.where(has_review)
        if from_requestee is not None:
            submissions = submissions.where(Submission.requestee_identifier == from_requestee)
        return session.scalars(submissions).all()


def list_submissions(
    mode: ListMode = ListMode.NEWEST, user: KeycloakUser = Depends(get_user_or_raise)
) -> Sequence[Submission]:
    # mypy does not do type narrowing properly: https://github.com/python/mypy/issues/12535
    user_filter = None if user.is_reviewer else user._subject_identifier
    if mode in [ListMode.NEWEST, ListMode.OLDEST]:
        submission = _get_single_submission(which=mode, from_requestee=user_filter)  # type: ignore[arg-type]
        return [submission] if submission else []
    if mode in [ListMode.PENDING, ListMode.COMPLETED, ListMode.ALL]:
        return _get_submissions_by_state(which=mode, from_requestee=user_filter)  # type: ignore[arg-type]
    raise ValueError(f"`mode` should be one of {ListMode!r} but is {mode!r}.")


def get_submission(
    identifier: int,
    user: KeycloakUser = Depends(get_user_or_raise),
    session: Session = Depends(get_session),
) -> Submission:
    submission = session.get(Submission, identifier)
    if not submission:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"No submission with identifier {identifier} found.",
        )
    if not user.is_reviewer and submission.requestee_identifier != user._subject_identifier:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail=f"You do not have permission to view submission with identifier {identifier}.",
        )
    return submission


def _review_resource(
    review: ReviewCreate,
    user: KeycloakUser = Depends(get_user_or_raise),
    session: Session = Depends(get_session),
):
    if not user.is_reviewer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must have reviewing privileges to use this endpoint.",
        )

    submission = session.get(Submission, review.submission_identifier)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No submission with identifier {review.submission_identifier} found.",
        )
    if not submission.is_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission is no longer pending review, no new decision may be made.",
        )
    register_user(user, session)

    aiod_entry = cast(AIoDEntryORM, session.get(AIoDEntryORM, submission.aiod_entry_identifier))
    if user_can_write(user, aiod_entry):
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


def retract_submission(
    submission_identifier: str,
    user: KeycloakUser = Depends(get_user_or_raise),
):
    with DbSession() as session:
        submission = session.get(Submission, submission_identifier)
        if not user_can_administer(user, submission.asset.aiod_entry):
            # Could choose to instead give same error as if resource does not exist.
            msg = f"You do not have permission to retract {submission.asset_type} {submission.asset.identifier}."
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

        if submission is None or not submission.is_pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot retract this asset, as it is not under review.",
            )

        retraction = Review(
            decision=Decision.RETRACTED,
            reviewer_identifier=user._subject_identifier,
            submission_identifier=submission.identifier,
        )
        submission.asset.aiod_entry.status = EntryStatus.DRAFT
        session.add(retraction)
        session.commit()
        return {
            "review_identifier": retraction.identifier,
            "submission_identifier": submission.identifier,
            "decision": retraction.decision,
        }
