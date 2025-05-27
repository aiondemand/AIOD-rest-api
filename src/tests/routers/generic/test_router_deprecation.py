import datetime

import pytest
from fastapi import FastAPI
from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from authentication import KeycloakUser
from tests.testutils.test_resource import RouterTestResource
from tests.testutils.users import kc_user_with_roles, logged_in_user


class DeprecatedRouter(RouterTestResource):
    """A deprecated router, just used for testing."""

    @property
    def version(self) -> int:
        return 1

    @property
    def deprecated_from(self, date=datetime.date(2022, 4, 21)) -> datetime.date | None:
        return date


@pytest.mark.parametrize(
    ("verb", "url", "user"),
    [
        ("get", "/test_resources/v1/", kc_user_with_roles()),
        ("get", "/test_resources/v1/1", kc_user_with_roles()),
        ("post", "/test_resources/v1/",  kc_user_with_roles()),
        ("put", "/test_resources/v1/1", kc_user_with_roles("update_test_resources")),
        ("delete", "/test_resources/v1/1",  kc_user_with_roles("delete_test_resources")),
    ]
)
def test_deprecated_router(
    engine_test_resource_filled: Engine, verb: str, url: str, user: KeycloakUser
):
    app = FastAPI()
    app.include_router(DeprecatedRouter().create(""))
    client = TestClient(app)

    kwargs = {}
    if verb in ("post", "put"):
        kwargs["json"] = {
            "title": "Another title",
            "platform": "example",
            "platform_resource_identifier": "2",
        }

    if verb in ("post", "put", "delete"):
        kwargs["headers"] = {"Authorization": "fake-token"}

    with logged_in_user(user):
        response = getattr(client, verb)(url, **kwargs)
    assert response.status_code == 200, response.json()
    assert "deprecated" in response.headers
    assert response.headers.get("deprecated") == "Thu, 21 Apr 2022 00:00:00 GMT"
