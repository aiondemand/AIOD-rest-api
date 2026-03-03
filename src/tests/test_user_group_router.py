from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from database.authorization import UserGroup, UserGroupMembership, Permission, PermissionType
from authentication import KeycloakUser
from tests.testutils.users import ALICE, BOB, ADMIN, _register_user_in_db, logged_in_user

def test_create_user_group_admin(client: TestClient, engine):
    with logged_in_user(ADMIN):
        response = client.post("/user_groups", json={"name": "test_group"})
        assert response.status_code == HTTPStatus.OK
        assert response.json()["name"] == "test_group"

        with Session(engine) as session:
            group = session.scalars(select(UserGroup).where(UserGroup.name == "test_group")).first()
            assert group is not None

def test_create_user_group_non_admin(client: TestClient):
    with logged_in_user(ALICE):
        response = client.post("/user_groups", json={"name": "test_group"})
        assert response.status_code == HTTPStatus.FORBIDDEN

def test_list_user_groups(client: TestClient, engine):
    with Session(engine) as session:
        session.add(UserGroup(name="group1"))
        session.add(UserGroup(name="group2"))
        session.commit()

    with logged_in_user(ALICE):
        response = client.get("/user_groups")
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 2
        names = [g["name"] for g in response.json()]
        assert "group1" in names
        assert "group2" in names

def test_get_user_group(client: TestClient, engine):
    with Session(engine) as session:
        group = UserGroup(name="group3")
        session.add(group)
        session.commit()
        session.refresh(group)
        
        # Add a test membership
        user = _register_user_in_db(ALICE, session)
        session.add(UserGroupMembership(user_group_identifier=group.identifier, user_identifier=user.subject_identifier))
        session.commit()

    with logged_in_user(BOB):
        response = client.get(f"/user_groups/{group.identifier}")
        assert response.status_code == HTTPStatus.OK
        assert response.json()["name"] == "group3"
        assert len(response.json()["users"]) == 1

def test_add_and_remove_user_to_group(client: TestClient, engine):
    with Session(engine) as session:
        group = UserGroup(name="group4")
        session.add(group)
        session.commit()
        session.refresh(group)

    # ALICE cannot add
    with logged_in_user(ALICE):
        response = client.post(f"/user_groups/{group.identifier}/users/bob")
        assert response.status_code == HTTPStatus.FORBIDDEN

    # ADMIN can add
    with logged_in_user(ADMIN):
        response = client.post(f"/user_groups/{group.identifier}/users/bob")
        assert response.status_code == HTTPStatus.OK

        with Session(engine) as session:
            memberships = session.scalars(select(UserGroupMembership).where(UserGroupMembership.user_group_identifier == group.identifier)).all()
            assert len(memberships) == 1

        response = client.delete(f"/user_groups/{group.identifier}/users/bob")
        assert response.status_code == HTTPStatus.OK

        with Session(engine) as session:
            memberships = session.scalars(select(UserGroupMembership).where(UserGroupMembership.user_group_identifier == group.identifier)).all()
            assert len(memberships) == 0
