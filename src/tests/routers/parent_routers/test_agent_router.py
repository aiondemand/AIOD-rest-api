import datetime

from sqlalchemy.engine import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from database.model.agent.organisation import Organisation
from database.model.agent.person import Person


def test_happy_path(
    client: TestClient,
    engine: Engine,
    organisation: Organisation,
    person: Person,
):

    organisation.name = "Organisation"
    person.name = "Person"
    with Session(engine) as session:
        session.add(organisation)
        session.merge(person)
        session.commit()

    response = client.get("/agents/v1/1")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["agent_identifier"] == 1
    assert response_json["name"] == "Organisation"

    response = client.get("/agents/v1/2")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["agent_identifier"] == 2
    assert response_json["name"] == "Person"


def test_ignore_deleted(
    client: TestClient,
    engine: Engine,
    organisation: Organisation,
    person: Person,
):

    organisation.name = "Organisation"
    organisation.date_deleted = datetime.datetime.now()
    person.name = "Person"
    with Session(engine) as session:
        session.add(organisation)
        session.merge(person)
        session.commit()

    response = client.get("/agents/v1/1")
    assert response.status_code == 404, response.json()

    response = client.get("/agents/v1/2")
    assert response.status_code == 200, response.json()
