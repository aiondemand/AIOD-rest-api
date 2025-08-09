from starlette.testclient import TestClient

from database.session import DbSession
from database.model.concept.aiod_entry import EntryStatus
from tests.testutils.test_resource import factory_test_resource


def test_get_all_happy_path(client_test_resource: TestClient):
    resources = [
        factory_test_resource(title="my_test_resource_1", status=EntryStatus.PUBLISHED,
                              platform_resource_identifier="2"),
        factory_test_resource(title="My second test resource", status=EntryStatus.PUBLISHED,
                              platform_resource_identifier="3"),
        factory_test_resource(title="My third test resource", status=EntryStatus.DRAFT,
                              platform_resource_identifier="4"),
    ]
    identifiers = [res.identifier for res in resources]

    with DbSession() as session:
        session.add_all(resources)
        session.commit()
    response = client_test_resource.get("/test_resources")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert len(response_json) == 2, "Expecting only two published assets"
    response_1, response_2 = response_json
    assert response_1["identifier"] == identifiers[0]
    assert response_1["title"] == "my_test_resource_1"
    assert response_2["identifier"] == identifiers[1]
    assert response_2["title"] == "My second test resource"
    assert "deprecated" not in response.headers
