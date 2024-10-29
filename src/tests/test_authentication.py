"""Unittests for the behaviour of get_user_or_raise()."""

import inspect
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from keycloak import KeycloakError
from starlette import status


from authentication import get_user_or_raise, keycloak_openid, User
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
        "edit_aiod_resources",
    }


def test_get_user_or_none_leaks_no_information():
    """
    Make sure an error is thrown if you change the fields on User. There may be good reasons to
    make a change, but please be very careful: we don't want to expose sensitive information to
    our application if it is not necessary. Moreover, the User class is returned by the
    authorization_test endpoint.
    """
    assert inspect.signature(get_user_or_raise).return_annotation == User
    assert set(inspect.get_annotations(User)) == {"name", "roles"}


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
async def test_keycloak_error():
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
