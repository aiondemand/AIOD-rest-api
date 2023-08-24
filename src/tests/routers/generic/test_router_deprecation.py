import datetime
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from authentication import keycloak_openid
from tests.testutils.test_resource import RouterTestResource


class DeprecatedRouter(RouterTestResource):
    """A deprecated router, just used for testing."""

    @property
    def version(self) -> int:
        return 1

    @property
    def deprecated_from(self, date=datetime.date(2022, 4, 21)) -> datetime.date | None:
        return date


@pytest.mark.parametrize(
    "verb,url",
    [
        ("get", "/test_resources/v1/"),
        # ("get", "/platforms/example/test_resources/v1"),
        ("get", "/test_resources/v1/1"),
        # ("get", "/platforms/example/test_resources/v1/1"),
        ("post", "/test_resources/v1/"),
        ("put", "/test_resources/v1/1"),
        ("delete", "/test_resources/v1/1"),
    ],
)
def test_deprecated_router(
    engine_test_resource_filled: Engine, verb: str, url: str, mocked_privileged_token: Mock
):
    keycloak_openid.userinfo = mocked_privileged_token
    app = FastAPI()
    app.include_router(DeprecatedRouter().create(engine_test_resource_filled, ""))
    client = TestClient(app)

    kwargs = {}
    if verb in ("post", "put"):
        kwargs["json"] = {
            "title": "Another title",
            "platform": "example",
            "platform_identifier": "2",
        }

    if verb in ("post", "put", "delete"):
        kwargs["headers"] = {"Authorization": "fake-token"}

    response = getattr(client, verb)(url, **kwargs)
    assert response.status_code == 200, response.json()
    assert "deprecated" in response.headers
    assert response.headers.get("deprecated") == "Thu, 21 Apr 2022 00:00:00 GMT"
