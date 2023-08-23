from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.platform.platform_names import PlatformName


def test_happy_path(client: TestClient, mocked_privileged_token: Mock):
    keycloak_openid.userinfo = mocked_privileged_token
    body = {"name": "my_favourite_platform"}
    response = client.post("/platforms/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    response = client.get("/platforms/v1")
    assert response.status_code == 200, response.json()
    platforms = {p["name"] for p in response.json()}
    assert platforms == {p.name for p in PlatformName}.union(["my_favourite_platform"])


@pytest.mark.skip(reason="TODO: while going to Metadata model v2")
@pytest.mark.parametrize(
    "url", ["/platforms/example/platforms/v1", "/platforms/example/platforms/v1/1"]
)
def test_get_platform_of_platform(client: TestClient, url: str):
    response = client.get(url)
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "Not Found"
