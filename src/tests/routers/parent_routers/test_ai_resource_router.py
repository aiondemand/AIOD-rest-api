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

    response = client.get("/ai_resources/v1/1")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["ai_resource_identifier"] == 1
    assert response_json["name"] == "Organisation"

    response = client.get("/ai_resources/v1/2")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["ai_resource_identifier"] == 2
    assert response_json["name"] == "Person"
