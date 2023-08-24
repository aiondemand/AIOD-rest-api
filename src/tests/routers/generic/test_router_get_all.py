from sqlalchemy.future import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from database.model.concept.status import Status
from tests.testutils.test_resource import test_resource_factory


def test_get_all_happy_path(
    client_test_resource: TestClient, engine_test_resource: Engine, draft: Status
):
    with Session(engine_test_resource) as session:
        session.add_all(
            [
                test_resource_factory(
                    title="my_test_resource_1", status=draft, platform_identifier="2"
                ),
                test_resource_factory(
                    title="My second test resource", status=draft, platform_identifier="3"
                ),
            ]
        )
        session.commit()
    response = client_test_resource.get("/test_resources/v0")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert len(response_json) == 2
    response_1, response_2 = response_json
    assert response_1["identifier"] == 1
    assert response_1["title"] == "my_test_resource_1"
    assert response_2["identifier"] == 2
    assert response_2["title"] == "My second test resource"
    assert "deprecated" not in response.headers
