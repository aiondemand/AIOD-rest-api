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
    person.name = "Person"
    with DbSession() as session:
        session.add(organisation)
        session.merge(person)
        session.commit()

        response = client.get(f"/ai_resources/{organisation.identifier}")
        assert response.status_code == 200, response.json()
        response_json = response.json()
        assert response_json["identifier"] == organisation.identifier
        assert response_json["ai_resource_identifier"] == organisation.identifier
        assert response_json["name"] == "Organisation"

        response = client.get(f"/ai_resources/{person.identifier}")
        assert response.status_code == 200, response.json()
        response_json = response.json()
        assert response_json["identifier"] == person.identifier
        assert response_json["ai_resource_identifier"] == person.identifier
        assert response_json["name"] == "Person"
