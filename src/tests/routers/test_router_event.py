import copy
from unittest.mock import Mock

from sqlalchemy.engine import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.person import Person


def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_resource: dict,
    person: Person,
):

    with Session(engine) as session:
        session.add(person)
        session.commit()

    keycloak_openid.userinfo = mocked_privileged_token
    body = copy.copy(body_resource)
    body["start_date"] = "2021-02-03T15:15:00"
    body["end_date"] = "2022-02-03T15:15:00"
    body["schedule"] = "Some text"
    body["registration_link"] = "https://example.com/registration-form"
    body["performer"] = [1]
    body["organiser"] = 1
    body["status"] = "scheduled"
    body["mode"] = "offline"

    response = client.post("/events/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/events/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["start_date"] == "2021-02-03T15:15:00"
    assert response_json["end_date"] == "2022-02-03T15:15:00"
    assert response_json["schedule"] == "Some text"
    assert response_json["registration_link"] == "https://example.com/registration-form"
    assert response_json["performer"] == [1]
    assert response_json["organiser"] == 1
    assert response_json["status"] == "scheduled"
    assert response_json["mode"] == "offline"
