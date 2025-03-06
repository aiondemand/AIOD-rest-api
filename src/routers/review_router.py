import enum
from http import HTTPStatus
from typing import Sequence, Literal

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select

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
