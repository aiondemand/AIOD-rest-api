from http import HTTPStatus

import pytest
from starlette.testclient import TestClient


def test_nondeprecated_versions(client: TestClient):
    response = client.get("/datasets")
    assert response.status_code == HTTPStatus.OK
    assert 'Deprecation' not in response.headers
    assert 'Sunset' not in response.headers
