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
    SubmissionCreate,
    AssetReview,
)
from database.model.concept.aiod_entry import EntryStatus, AIoDEntryORM
from database.model.concept.concept import AIoDConcept
from routers.helper_functions import get_asset_type_by_abbreviation, get_router_by_type
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

    router.post(
        path=f"/submissions",
        tags=["Reviewing"],
        description=f"Submit an asset for review.",
    )(_submit_resource)

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


def _submit_resource(
    submission: SubmissionCreate,
    user: KeycloakUser = Depends(get_user_or_raise),
):
    id_to_type = {
        identifier: get_asset_type_by_abbreviation().get(identifier.split("_")[0])
        for identifier in submission.asset_identifiers
    }
    invalid_identifier = next(
        (identifier for identifier, type_ in id_to_type.items() if type_ is None), None
    )
    if invalid_identifier:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"{invalid_identifier} is not a valid resource identifier.",
        )

    with DbSession() as session:
        review_request = Submission(
            requestee_identifier=user._subject_identifier,
            comment=submission.comment,
        )
        for identifier, asset_type in id_to_type.items():
            router = get_router_by_type()[cast(type[AIoDConcept], asset_type)]
            resource = router._retrieve_resource(identifier=identifier, session=session)  # type: ignore

            if not resource.aiod_entry.status == EntryStatus.DRAFT:
                msg = (
                    f"Cannot submit {router.resource_name} {identifier} "
                    f"since it has '{resource.aiod_entry.status}' status."
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

            if not user_can_administer(user, resource.aiod_entry):
                # Could choose to instead give same error as if resource does not exist.
                msg = f"You do not have permission to submit {router.resource_name} {identifier}."
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

            resource.aiod_entry.status = EntryStatus.SUBMITTED
            review_request._assets.append(
                AssetReview(
                    asset_identifier=resource.identifier,
                    aiod_entry_identifier=resource.aiod_entry.identifier,
                )
            )
        session.add(review_request)
        session.commit()
        return {"submission_identifier": review_request.identifier}


def _review_resource(
    review: ReviewCreate,
    user: KeycloakUser = Depends(get_user_or_raise),
    session: Session = Depends(get_session),
):
    if not (user.is_reviewer or user.is_admin):
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

    for asset_to_review in submission._assets:
        aiod_entry = cast(
            AIoDEntryORM, session.get(AIoDEntryORM, asset_to_review.aiod_entry_identifier)
        )
        if user_can_write(user, aiod_entry):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Review request contains asset {asset_to_review.asset_identifier!r}, "
                    "which you own. You do not have permission to review your own assets."
                ),
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
        if submission is None:
            return HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Submission {submission_identifier} not found.",
            )

        if not submission.is_pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot retract this submission, as it is not under review.",
            )

        if not any(
            user_can_administer(user, session.get(AIoDEntryORM, a.aiod_entry_identifier))
            for a in submission._assets
        ):
            msg = f"You must be administrator of at least one asset in the review to retract the submission."
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

        retraction = Review(
            decision=Decision.RETRACTED,
            reviewer_identifier=user._subject_identifier,
            submission_identifier=submission.identifier,
        )
        for asset in submission.assets:
            asset.aiod_entry.status = EntryStatus.DRAFT
        session.add(retraction)
        session.commit()
        return {
            "review_identifier": retraction.identifier,
            "submission_identifier": submission.identifier,
            "decision": retraction.decision,
        }
