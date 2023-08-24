import copy
from unittest.mock import Mock

from sqlalchemy.engine import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person


def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_resource: dict,
    person: Person,
    organisation: Organisation,
):
    keycloak_openid.userinfo = mocked_privileged_token

    with Session(engine) as session:
        session.add(person)
        session.merge(organisation)
        session.commit()

    body = copy.deepcopy(body_resource)
    body["price_per_hour_euro"] = 70.75
    body["size"] = 5
    body["organisation"] = 1
    body["member"] = [1]

    response = client.post("/teams/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/teams/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["price_per_hour_euro"] == 70.75
    assert response_json["size"] == 5
    assert response_json["organisation"] == 1
    assert response_json["member"] == [1]
