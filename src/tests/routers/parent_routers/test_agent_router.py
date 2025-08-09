import datetime

from starlette.testclient import TestClient

from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.session import DbSession


def test_happy_path(
    client: TestClient,
    organisation: Organisation,
    person: Person,
):

    organisation.name = "Organisation"
    organisation.legal_name = "EU"
    person.name = "Person"
    person.given_name = "Alice"

    with DbSession() as session:
        session.add(organisation)
        session.merge(person)
        session.commit()

        response = client.get(f"/agents/{organisation.identifier}")
        assert response.status_code == 200, response.json()
        response_json = response.json()
        assert response_json["identifier"] == organisation.identifier
        assert response_json["agent_identifier"] == organisation.identifier
        assert response_json["name"] == "Organisation"
        assert response_json["legal_name"] == "EU"

        response = client.get(f"/agents/{person.identifier}")
        assert response.status_code == 200, response.json()
        response_json = response.json()
        assert response_json["identifier"] == person.identifier
        assert response_json["agent_identifier"] == person.identifier
        assert response_json["name"] == "Person"
        assert response_json["given_name"] == "Alice"


def test_ignore_deleted(
    client: TestClient,
    organisation: Organisation,
    person: Person,
):

    organisation.name = "Organisation"
    organisation.date_deleted = datetime.datetime.now()
    person.name = "Person"
    with DbSession() as session:
        session.add(organisation)
        session.merge(person)
        session.commit()

        response = client.get(f"/agents/{organisation.identifier}")
        assert response.status_code == 404, response.json()

        response = client.get(f"/agents/{person.identifier}")
        assert response.status_code == 200, response.json()
