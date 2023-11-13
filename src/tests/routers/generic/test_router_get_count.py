import datetime

from sqlalchemy.future import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from database.model.concept.status import Status
from tests.testutils.test_resource import test_resource_factory


def test_get_count_happy_path(
    client_test_resource: TestClient, engine_test_resource: Engine, draft: Status
):
    with Session(engine_test_resource) as session:
        session.add_all(
            [
                test_resource_factory(
                    title="my_test_resource_1", status=draft, platform_resource_identifier="1"
                ),
                test_resource_factory(
                    title="My second test resource", status=draft, platform_resource_identifier="2"
                ),
                test_resource_factory(
                    title="My third test resource",
                    status=draft,
                    platform_resource_identifier="3",
                    date_deleted=datetime.datetime.now(),
                ),
            ]
        )
        session.commit()
    response = client_test_resource.get("/counts/test_resources/v1")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json == 2
    assert "deprecated" not in response.headers
