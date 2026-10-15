"""Unittests for the behaviour of get_user_or_raise()."""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from keycloak import KeycloakError
from starlette import status


from authentication import get_user_or_raise, keycloak_openid
from tests.testutils.users import ALICE, logged_in_user
from tests.testutils.mock_keycloak import MockedKeycloak, TestUserType


@pytest.mark.asyncio
async def test_happy_path():
    with MockedKeycloak() as _:
        user = await get_user_or_raise(token="Bearer mocked")
    assert user.name == "user"
    assert set(user.roles) == {"offline_access", "uma_authorization", "default-roles-aiod"}


@pytest.mark.asyncio
async def test_happy_path_privileged():
    with MockedKeycloak(type_=TestUserType.privileged) as _:
        user = await get_user_or_raise(token="Bearer mocked")
    assert user.name == "user"
    assert set(user.roles) == {
        "offline_access",
        "uma_authorization",
        "default-roles-aiod",
    }


def test_get_user_or_none_leaks_no_information(client):
    """
    Make sure an error is thrown if you change the fields on KeycloakUser. There may be good reasons
    to make a change, but please be very careful: we don't want to expose sensitive information to
    our application if it is not necessary. Moreover, the KeycloakUser class is returned by the
    authorization_test endpoint.
    """
    with logged_in_user(ALICE):
        response = client.get("/authorization_test", headers={"Authorization": "Bearer mocked"})
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert set(response.json().keys()) == {"name", "roles"}


@pytest.mark.asyncio
async def test_inactive_user():
    with MockedKeycloak(type_=TestUserType.inactive) as _:
        with pytest.raises(HTTPException) as exception_info:
            await get_user_or_raise(token="Bearer mocked")

        assert exception_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exception_info.value.detail == (
            "Invalid userinfo or inactive user - "
            "This endpoint requires authorization. You need to be logged in."
        )


@pytest.mark.asyncio
async def test_unauthenticated():
    with pytest.raises(HTTPException) as exception_info:
        await get_user_or_raise(token=None)
    assert exception_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        exception_info.value.detail
        == "No token found - This endpoint requires authorization. You need to be logged in."
    )


@pytest.mark.asyncio
async def test_federated_user_without_username():
    """EGI Check-in tokens often omit username; authorization_test must still return a name."""
    keycloak_openid.introspect = Mock(
        return_value={
            "active": True,
            "sub": "egi-user-sub",
            "preferred_username": "someone@example.org",
            "username": None,
            "realm_access": {"roles": ["default-roles-aiod"]},
        }
    )
    user = await get_user_or_raise(token="Bearer mocked")
    assert user.name == "someone@example.org"
    assert user._subject_identifier == "egi-user-sub"


@pytest.mark.asyncio
async def test_keycloak_error(mocked_token: Mock):
    """
    On any problem, keycloak_openid.introspect raises an error.

    Refer to https://connect2id.com/products/server/docs/api/token-introspection for a list of
    possible errors. Only created a single testcase because we handle all errors the same way.
    """
    keycloak_openid.introspect = Mock(
        side_effect=KeycloakError(
            error_message="unused message", response_code=status.HTTP_403_FORBIDDEN
        )
    )
    with pytest.raises(HTTPException) as exception_info:
        await get_user_or_raise(token="Bearer mocked")
    assert exception_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception_info.value.detail == "Invalid authentication token"
