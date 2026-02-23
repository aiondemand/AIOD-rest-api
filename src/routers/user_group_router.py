import re
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel

from authentication import KeycloakUser, get_user_or_raise, get_user_by_username, get_user_by_sub
from database.authorization import UserGroup, UserGroupMembership, User, register_user
from database.session import get_session
from dependencies.pagination import PaginationParams
from versioning import Version

class UserGroupCreate(BaseModel):
    name: str

class UserGroupRead(BaseModel):
    identifier: int
    name: str

class UserGroupReadWithUsers(UserGroupRead):
    users: list[str] = []

def create(url_prefix: str, version: Version) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/user_groups",
        tags=["User Groups"],
        description="Create a new user group.",
        response_model=UserGroupRead,
    )
    def create_user_group(
        group: UserGroupCreate,
        session: Session = Depends(get_session),
        current_user: KeycloakUser = Depends(get_user_or_raise),
    ):
        if not current_user.is_admin:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Only admins can create user groups.")
        
        existing = session.scalars(select(UserGroup).where(UserGroup.name == group.name)).first()
        if existing:
            raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=f"User group '{group.name}' already exists.")
            
        new_group = UserGroup(name=group.name)
        session.add(new_group)
        session.commit()
        session.refresh(new_group)
        return new_group

    @router.get(
        "/user_groups",
        tags=["User Groups"],
        description="List all user groups.",
        response_model=list[UserGroupRead],
    )
    def list_user_groups(
        pagination: PaginationParams = Depends(),
        session: Session = Depends(get_session),
        current_user: KeycloakUser = Depends(get_user_or_raise),
    ):
        stmt = select(UserGroup).offset(pagination.offset)
        if pagination.limit is not None:
            stmt = stmt.limit(pagination.limit)
        groups = session.scalars(stmt).all()
        return groups

    @router.get(
        "/user_groups/{identifier}",
        tags=["User Groups"],
        description="Get a user group by its identifier.",
        response_model=UserGroupReadWithUsers,
    )
    def get_user_group(
        identifier: int,
        session: Session = Depends(get_session),
        current_user: KeycloakUser = Depends(get_user_or_raise),
    ):
        group = session.get(UserGroup, identifier)
        if not group:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User group {identifier} not found.")
        
        users = []
        for u in group.users:
            kc_user = get_user_by_sub(u.subject_identifier)
            if kc_user and kc_user.name:
                users.append(kc_user.name)
            else:
                users.append(u.subject_identifier)
                
        return UserGroupReadWithUsers(
            identifier=group.identifier,
            name=group.name,
            users=users,
        )

    @router.delete(
        "/user_groups/{identifier}",
        tags=["User Groups"],
        description="Delete a user group.",
    )
    def delete_user_group(
        identifier: int,
        session: Session = Depends(get_session),
        current_user: KeycloakUser = Depends(get_user_or_raise),
    ):
        if not current_user.is_admin:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Only admins can delete user groups.")
            
        group = session.get(UserGroup, identifier)
        if not group:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User group {identifier} not found.")
            
        session.delete(group)
        session.commit()

    @router.post(
        "/user_groups/{identifier}/users/{username}",
        tags=["User Groups"],
        description="Add a user to a user group.",
    )
    def add_user_to_group(
        identifier: int,
        username: str,
        session: Session = Depends(get_session),
        current_user: KeycloakUser = Depends(get_user_or_raise),
    ):
        if not current_user.is_admin:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Only admins can update user groups.")
            
        group = session.get(UserGroup, identifier)
        if not group:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User group {identifier} not found.")
            
        sub_pattern = r"\S{8}(-\S{4}){3}-\S{12}"
        if re.match(sub_pattern, username):
            kc_user = KeycloakUser(name="unknown", roles=set(), _subject_identifier=username)
        else:
            kc_user = get_user_by_username(username)
            if not kc_user:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User {username} not found.")
                
        db_user = register_user(kc_user, session)
        session.commit()
        
        if not any(u.subject_identifier == db_user.subject_identifier for u in group.users):
            membership = UserGroupMembership(
                user_group_identifier=identifier,
                user_identifier=db_user.subject_identifier
            )
            session.add(membership)
            session.commit()
            
    @router.delete(
        "/user_groups/{identifier}/users/{username}",
        tags=["User Groups"],
        description="Remove a user from a user group.",
    )
    def remove_user_from_group(
        identifier: int,
        username: str,
        session: Session = Depends(get_session),
        current_user: KeycloakUser = Depends(get_user_or_raise),
    ):
        if not current_user.is_admin:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Only admins can update user groups.")
            
        group = session.get(UserGroup, identifier)
        if not group:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User group {identifier} not found.")
            
        sub_pattern = r"\S{8}(-\S{4}){3}-\S{12}"
        if re.match(sub_pattern, username):
            subject = username
        else:
            kc_user = get_user_by_username(username)
            if not kc_user:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User {username} not found.")
            subject = kc_user._subject_identifier
                
        membership = session.scalars(
            select(UserGroupMembership).where(
                UserGroupMembership.user_group_identifier == identifier,
                UserGroupMembership.user_identifier == subject
            )
        ).first()
        
        if membership:
            session.delete(membership)
            session.commit()

    return router
