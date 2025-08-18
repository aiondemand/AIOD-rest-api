import sqlalchemy.exc
from fastapi import APIRouter, Depends, HTTPException
from typing import List, cast
from sqlmodel import Session, select, Field, SQLModel

from authentication import KeycloakUser, get_user_or_raise
from database.session import get_session
from database.model.bookmark.bookmark import Bookmark
from http import HTTPStatus
from datetime import datetime
from routers.helper_functions import get_asset_type_by_abbreviation
from versioning import Version


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
        user: KeycloakUser = Depends(get_user_or_raise), session: Session = Depends(get_session)
    ) -> List[BookmarkRead]:
        return session.exec(
            select(Bookmark).where(Bookmark.user_identifier == user._subject_identifier)
        ).all()

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

        try:
            bookmark = Bookmark(
                user_identifier=user._subject_identifier,
                resource_identifier=resource_identifier,
            )
            session.add(bookmark)
            session.commit()
        except sqlalchemy.exc.IntegrityError:  # The entry already exists
            session.rollback()
            bookmark = session.get(Bookmark, (user._subject_identifier, resource_identifier))
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
