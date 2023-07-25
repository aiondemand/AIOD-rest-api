import pytest
from sqlmodel import Session
from starlette.testclient import TestClient
from sqlalchemy.future import Engine

from database.model import AIAssetOldTable
from tests.testutils.test_resource import TestResource
from authentication import keycloak_openid
from unittest.mock import Mock


@pytest.mark.parametrize("identifier", [1, 2])
def test_happy_path(
    client_test_resource: TestClient,
    engine_test_resource: Engine,
    identifier: int,
    mocked_privileged_token: Mock,
):
    keycloak_openid.userinfo = mocked_privileged_token

    with Session(engine_test_resource) as session:
        session.add_all(
            [
                AIAssetOldTable(type="test_resource"),
                AIAssetOldTable(type="test_resource"),
                TestResource(title="my_test_resource", platform="example", platform_identifier=1),
                TestResource(
                    title="second_test_resource", platform="example", platform_identifier=2
                ),
            ]
        )
        session.commit()
    response = client_test_resource.delete(
        f"/test_resources/v0/{identifier}", headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200
    response = client_test_resource.get("/test_resources/v0/")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 1
    assert {r["identifier"] for r in response_json} == {1, 2} - {identifier}


@pytest.mark.parametrize("identifier", [3, 4])
def test_non_existent(
    client_test_resource: TestClient,
    engine_test_resource: Engine,
    identifier: int,
    mocked_privileged_token: Mock,
):
    keycloak_openid.userinfo = mocked_privileged_token
    with Session(engine_test_resource) as session:
        session.add_all(
            [
                AIAssetOldTable(type="test_resource"),
                AIAssetOldTable(type="test_resource"),
                TestResource(title="my_test_resource", platform="example", platform_identifier=1),
                TestResource(
                    title="second_test_resource", platform="example", platform_identifier=2
                ),
            ]
        )
        session.commit()
    response = client_test_resource.delete(
        f"/test_resources/v0/{identifier}", headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == f"Test_resource '{identifier}' not found in the database."
