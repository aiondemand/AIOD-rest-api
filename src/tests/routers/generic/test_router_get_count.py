import datetime

from starlette.testclient import TestClient

from database.model.agent.contact import Contact
from database.model.agent.person import Person
from database.model.concept.aiod_entry import  EntryStatus
from database.model.knowledge_asset.publication import Publication
from database.session import DbSession
from tests.testutils.test_resource import factory_test_resource
from tests.testutils.users import register_asset


def test_get_count_happy_path(client_test_resource: TestClient):
    with DbSession() as session:
        session.add_all(
            [
                factory_test_resource(title="my_test_resource_1", status=EntryStatus.PUBLISHED,
                                      platform_resource_identifier="1"),
                factory_test_resource(title="My second test resource", status=EntryStatus.PUBLISHED,
                                      platform_resource_identifier="2"),
                factory_test_resource(title="My third test resource", status=EntryStatus.PUBLISHED,
                                      platform_resource_identifier="3",
                                      date_deleted=datetime.datetime.now()),
                factory_test_resource(title="My fourth test resource", status=EntryStatus.DRAFT,
                                      platform_resource_identifier="4"),
            ]
        )
        session.commit()
    response = client_test_resource.get("/counts/test_resources")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json == 2
    assert "deprecated" not in response.headers


def test_get_count_detailed_happy_path(client_test_resource: TestClient):
    with DbSession() as session:
        session.add_all(
            [
                factory_test_resource(title="my_test_resource_1", status=EntryStatus.PUBLISHED,
                                      platform_resource_identifier="1"),
                factory_test_resource(title="My second test resource", status=EntryStatus.PUBLISHED,
                                      platform_resource_identifier="2"),
                factory_test_resource(title="My third test resource", status=EntryStatus.PUBLISHED,
                                      platform="openml", platform_resource_identifier="3",
                                      date_deleted=datetime.datetime.now()),
                factory_test_resource(title="My third test resource", status=EntryStatus.PUBLISHED,
                                      platform="openml", platform_resource_identifier="4"),
                factory_test_resource(title="My fourth test resource", status=EntryStatus.PUBLISHED,
                                      platform=None, platform_resource_identifier=None),
            ]
        )
        session.commit()
    response = client_test_resource.get("/counts/test_resources?detailed=true")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json == {"aiod": 1, "example": 2, "openml": 1}
    assert "deprecated" not in response.headers

from database.model.concept.aiod_entry import EntryStatus, AIoDEntryORM
# default platfrom is "aiod"
def test_get_count_total(
    client: TestClient,
    person: Person,
    publication: Publication,
    contact: Contact,
):

    register_asset(person)
    register_asset(publication)
    register_asset(contact)

    resources = [
        Publication(name="2", platform="example", platform_resource_identifier=2),
        Publication(name="3", platform="example", platform_resource_identifier=3)
    ]
    for res in resources:
        res.aiod_entry = AIoDEntryORM()
        res.aiod_entry.status = EntryStatus.PUBLISHED

    with DbSession() as session:
        session.add_all(resources)
        session.commit()

    response = client.get("/counts")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json == {
        "contacts": {"aiod": 1},
        "persons": {"aiod": 1},
        "publications": {"aiod": 1, "example": 2},
    }
    assert "deprecated" not in response.headers
