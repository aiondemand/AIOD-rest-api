"""Mocking the Keycloak instance."""

import enum
import json
from contextlib import contextmanager
from pathlib import Path

import pytest
import responses

from tests.testutils.paths import path_test_resources


class TestUserType(enum.Enum):
    __test__ = False
    user = "user.json"
    privileged = "user_privileged.json"
    inactive = "user_inactive.json"


@contextmanager
def MockedKeycloak(type_: TestUserType = TestUserType.user) -> responses.RequestsMock:
    """
    Mock the keycloak instance.
    """
    path_user = path_test_resources() / "authentication" / type_.value
    return _mocked_user(path_user)


def _mocked_user(path_user_json: Path) -> responses.RequestsMock:
    with path_user_json.open("r") as f:
        response = json.load(f)

    with responses.RequestsMock() as request_mock:
        request_mock.add(
            responses.POST,
            "http://keycloak:8080/aiod-auth/realms/aiod/protocol/openid-connect/token/introspect",
            json=response,
        )
        yield request_mock


def _mocked_admin() -> responses.RequestsMock:
    cached_response = path_test_resources() / "authentication" / "admin_connect.json"
    with cached_response.open("r") as f:
        response = json.load(f)

    with responses.RequestsMock() as request_mock:
        request_mock.add(
            responses.POST,
            "http://keycloak:8080/aiod-auth/realms/master/protocol/openid-connect/token",
            json=response,
        )
        yield request_mock
