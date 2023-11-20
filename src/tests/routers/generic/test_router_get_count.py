import datetime

from sqlalchemy.future import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from database.model.agent.contact import Contact
from database.model.agent.person import Person
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.concept.status import Status
from database.model.knowledge_asset.publication import Publication
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


def test_get_count_detailed_happy_path(
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
                    platform="openml",
                ),
                test_resource_factory(
                    title="My third test resource",
                    status=draft,
                    platform_resource_identifier="4",
                    platform="openml",
                ),
                test_resource_factory(
                    title="My fourth test resource",
                    status=draft,
                    platform=None,
                    platform_resource_identifier=None,
                ),
            ]
        )
        session.commit()
    response = client_test_resource.get("/counts/test_resources/v1?detailed=true")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json == {"aiod": 1, "example": 2, "openml": 1}
    assert "deprecated" not in response.headers


def test_get_count_total(
    client: TestClient,
    engine: Engine,
    person: Person,
    publication: Publication,
    contact: Contact,
):

    with Session(engine) as session:
        session.add(person)
        session.merge(publication)
        session.add(Publication(name="2", aiod_enty=AIoDEntryORM(type="publication")))
        session.add(Publication(name="3", aiod_enty=AIoDEntryORM(type="publication")))
        session.add(contact)
        session.commit()

    response = client.get("/counts/v1")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json == {
        "contacts": {"example": 1},
        "persons": {"example": 1},
        "publications": {"aiod": 2, "example": 1},
    }
    assert "deprecated" not in response.headers
