import logging

import sqlalchemy.exc
from fastapi import APIRouter, Depends, HTTPException
from typing import List, cast
from sqlmodel import Session, select, Field, SQLModel

from authentication import KeycloakUser, get_user_or_raise
from database.session import get_session
from database.authorization import register_user
from database.model.bookmark.bookmark import Bookmark
from http import HTTPStatus
from datetime import datetime

from dependencies.pagination import PaginationParams
from database.model.helper_functions import get_asset_type_by_abbreviation
from versioning import Version


logger = logging.getLogger(__name__)


class BookmarkRead(SQLModel):
    resource_identifier: str = Field(description="The identifier of the resource being bookmarked.")
    created_at: datetime = Field(
        description="The time when the bookmark was created in ISO 8601 format."
    )

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


def create(url_prefix: str = "", version: Version = Version.LATEST) -> APIRouter:
    router = APIRouter()
    path = "/bookmarks"

    @router.get(
        path,
        tags=["User"],
        description="Return all your bookmarks.",
        response_model=List[BookmarkRead],
    )
    def list_bookmarks(
        pagination: PaginationParams,
        user: KeycloakUser = Depends(get_user_or_raise),
        session: Session = Depends(get_session),
    ) -> List[BookmarkRead]:
        stmt = (
            select(Bookmark)
            .where(Bookmark.user_identifier == user._subject_identifier)
            .order_by(Bookmark.created_at)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return session.exec(stmt).all()

    @router.post(
        path,
        tags=["User"],
        response_model=BookmarkRead,
        description="Add the asset to the logged-in user's bookmarks."
        "If it was already bookmarked, return the existing bookmark.",
        status_code=HTTPStatus.OK,
    )
    def create_bookmark(
        resource_identifier: str,
        user: KeycloakUser = Depends(get_user_or_raise),
        session: Session = Depends(get_session),
    ) -> BookmarkRead:
        if not resource_identifier_exists_in_database(resource_identifier, session):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Resource {resource_identifier} does not exist.",
            )

        register_user(user, session)
        try:
            bookmark = Bookmark(
                user_identifier=user._subject_identifier,
                resource_identifier=resource_identifier,
            )
            session.add(bookmark)
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            session.rollback()
            # Most likely there is an error here because the bookmark already exists.
            bookmark = session.get(Bookmark, (user._subject_identifier, resource_identifier))
            if not bookmark:
                logger.warning(f"Unexpected error creating bookmark: {e}")
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=f"Unexpected error creating bookmark ({user}, {resource_identifier!r}): {e}",
                )
        return cast(BookmarkRead, bookmark)

    @router.delete(
        path,
        tags=["User"],
        description="Delete a bookmark for the logged-in user by resource identifier."
        "Also returns HTTP status code OK (200) if no such bookmark existed.",
        status_code=HTTPStatus.OK,
    )
    def delete_bookmark(
        resource_identifier: str,
        user: KeycloakUser = Depends(get_user_or_raise),
        session: Session = Depends(get_session),
    ):
        bookmark = session.get(Bookmark, (user._subject_identifier, resource_identifier))
        if bookmark:
            session.delete(bookmark)
            session.commit()
        return None

    return router


def resource_identifier_exists_in_database(resource_identifier: str, session: Session) -> bool:
    """
    Returns True if the given identifier exists in any of the tables.
    """
    asset_type = get_asset_type_by_abbreviation().get(resource_identifier.split("_")[0], None)
    if asset_type:
        query = select(asset_type).where(asset_type.identifier == resource_identifier)
        return session.exec(query).first() is not None

    return False
