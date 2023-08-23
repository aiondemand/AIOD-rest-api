from unittest.mock import Mock

import pytest
from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from authentication import keycloak_openid


@pytest.mark.skip(reason="This test isn't finished yet, we need to mock ES")
def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_resource: dict,
):
    keycloak_openid.userinfo = mocked_privileged_token

    response = client.get(
        "/search/publications/v1", params={"title": "in"}, headers={"Authorization": "Fake token"}
    )
    # TODO(jos): mock the ES results. But first we need some results
    assert response.status_code == 200, response.json()
