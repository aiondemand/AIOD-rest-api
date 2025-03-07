import enum
from http import HTTPStatus
from typing import Sequence, Literal

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select, Session

from authentication import KeycloakUser, get_user_or_raise
from database.session import DbSession, get_session
from database.review import Submission, Review, SubmissionView, SubmissionBase


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
        query = select(Submission).where(~has_review)

        if which == ListMode.NEWEST:
            query = query.order_by(Submission.request_date.desc())  # type: ignore[attr-defined]
        if from_requestee is not None:
            query = query.where(Submission.requestee_identifier == from_requestee)

        return session.scalars(query).first()


def _get_submissions_by_state(
    *,
    which: Literal[ListMode.COMPLETED, ListMode.PENDING],
    from_requestee: str | None = None,
) -> Sequence[Submission]:
    with DbSession() as session:
        has_review = select(1).where(Submission.identifier == Review.submission_identifier).exists()
        if which == ListMode.PENDING:
            submissions = select(Submission).where(~has_review)
        if which == ListMode.COMPLETED:
            submissions = select(Submission).where(has_review)
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
    if mode in [ListMode.PENDING, ListMode.COMPLETED]:
        return _get_submissions_by_state(which=mode, from_requestee=user_filter)  # type: ignore[arg-type]
    raise ValueError(f"`mode` should be one of {ListMode!r} but is {mode!r}.")


def get_submission(
    identifier: int,
    user: KeycloakUser = Depends(get_user_or_raise),
    session: Session = Depends(get_session),
) -> Submission:
    query = select(Submission).where(Submission.identifier == identifier)
    submission = session.scalars(query).first()
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
