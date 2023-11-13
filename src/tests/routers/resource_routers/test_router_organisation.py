import copy
from unittest.mock import Mock

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation


def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    organisation: Organisation,
    contact: Contact,
    body_agent: dict,
):
    keycloak_openid.userinfo = mocked_privileged_token

    with Session(engine) as session:
        session.add(organisation)  # The new organisation will be a member of this organisation
        session.add(contact)
        session.commit()

    body = copy.copy(body_agent)
    body["platform_resource_identifier"] = "2"
    body["date_founded"] = "2023-01-01"
    body["legal_name"] = "A name for the organisation"
    body["ai_relevance"] = "Part of CLAIRE"
    body["type"] = "Research Institute"
    body["member"] = [1]
    body["contact_details"] = 1

    response = client.post("/organisations/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/organisations/v1/2")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == 2
    assert response_json["ai_resource_identifier"] == 2
    assert response_json["agent_identifier"] == 2

    assert response_json["date_founded"] == "2023-01-01"
    assert response_json["legal_name"] == "A name for the organisation"
    assert response_json["ai_relevance"] == "Part of CLAIRE"
    assert response_json["type"] == "Research Institute"
    assert response_json["member"] == [1]
    assert response_json["contact_details"] == 1

    # response = client.delete("/organisations/v1/1", headers={"Authorization": "Fake token"})
    # assert response.status_code == 200
    # response = client.get("/organisations/v1/2")
    # assert response.status_code == 200, response.json()
    # response_json = response.json()
    # TODO(jos): make sure Agent is deleted on CASCADE

    body["type"] = "Association"
    response = client.put("organisations/v1/2", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    response = client.get("organisations/v1/2")
    assert response.json()["type"] == "Association"

    response = client.delete("/organisations/v1/2", headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
