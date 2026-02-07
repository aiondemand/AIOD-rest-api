import copy
from http import HTTPStatus

import pytest
from freezegun import freeze_time
from starlette.testclient import TestClient

from config import CONFIG
from tests.testutils.users import logged_in_user, kc_connector_with_roles


@pytest.fixture
def rate_limit_one_per_hour():
    original = copy.deepcopy(CONFIG.get("rate_limit", {}))
    CONFIG.setdefault("rate_limit", {})
    CONFIG["rate_limit"]["enabled"] = True
    CONFIG["rate_limit"]["uploads_per_window"] = 1
    CONFIG["rate_limit"]["window_seconds"] = 3600
    yield
    if original:
        CONFIG["rate_limit"] = original
    else:
        CONFIG.pop("rate_limit", None)


def test_rate_limit_reached(client_test_resource: TestClient, rate_limit_one_per_hour):
    headers = {"Authorization": "Fake token"}
    with logged_in_user():
        first = client_test_resource.post(
            "/test_resources", json={"title": "title1"}, headers=headers
        )
        assert first.status_code == HTTPStatus.OK, first.json()

        second = client_test_resource.post(
            "/test_resources", json={"title": "title2"}, headers=headers
        )
        assert second.status_code == HTTPStatus.TOO_MANY_REQUESTS, second.json()
        assert "Upload rate limit exceeded" in second.json()["detail"]


def test_rate_limit_resets_after_window(client_test_resource: TestClient, rate_limit_one_per_hour):
    headers = {"Authorization": "Fake token"}
    with freeze_time("2026-02-07T10:00:00Z"):
        with logged_in_user():
            first = client_test_resource.post(
                "/test_resources", json={"title": "title1"}, headers=headers
            )
            assert first.status_code == HTTPStatus.OK, first.json()

            second = client_test_resource.post(
                "/test_resources", json={"title": "title2"}, headers=headers
            )
            assert second.status_code == HTTPStatus.TOO_MANY_REQUESTS, second.json()

    with freeze_time("2026-02-07T11:00:01Z"):
        with logged_in_user():
            third = client_test_resource.post(
                "/test_resources", json={"title": "title3"}, headers=headers
            )
            assert third.status_code == HTTPStatus.OK, third.json()


def test_connector_bypasses_rate_limit(client_test_resource: TestClient, rate_limit_one_per_hour):
    headers = {"Authorization": "Fake token"}
    connector_user = kc_connector_with_roles()
    with logged_in_user(connector_user):
        first = client_test_resource.post(
            "/test_resources",
            json={"title": "title1", "platform": "example", "platform_resource_identifier": "1"},
            headers=headers,
        )
        assert first.status_code == HTTPStatus.OK, first.json()

        second = client_test_resource.post(
            "/test_resources",
            json={"title": "title2", "platform": "example", "platform_resource_identifier": "2"},
            headers=headers,
        )
        assert second.status_code == HTTPStatus.OK, second.json()
