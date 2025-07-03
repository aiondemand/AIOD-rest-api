import copy
from unittest.mock import Mock

from starlette.testclient import TestClient

from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation
from database.session import DbSession


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    organisation: Organisation,
    contact: Contact,
    body_agent: dict,
    auto_publish: None,
):
    body = copy.copy(body_agent)
    body["date_founded"] = "2023-01-01"
    body["legal_name"] = "A name for the organisation"
    body["ai_relevance"] = "Part of CLAIRE"
    body["type"] = "Research Institute"
    with DbSession() as session:
        session.add(organisation)  # The new organisation will be a member of this organisation
        session.add(contact)
        session.commit()

        body["member"] = [organisation.identifier]
        body["contact_details"] = contact.identifier
        body["contact"] = [contact.identifier]

    response = client.post("/organisations", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/organisations/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == identifier
    assert response_json["ai_resource_identifier"] == identifier
    assert response_json["agent_identifier"] == identifier

    assert response_json["date_founded"] == "2023-01-01"
    assert response_json["legal_name"] == "A name for the organisation"
    assert response_json["ai_relevance"] == "Part of CLAIRE"
    assert response_json["type"] == "research institute"
    assert response_json["member"] == body["member"]
    assert response_json["contact_details"] == body["contact_details"]
    assert response_json["contacts"][0]["name"] == "Aaron Bar"
    assert response_json["contacts"][0]["telephone"] == ["0032 xxxx xxxx"]
    assert response_json["contacts"][0]["email"] == ["a@b.com"]
    assert response_json["contacts"][0]["location"] == [
        {
            "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
            "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
        }
    ]

    # response = client.delete("/organisations/1", headers={"Authorization": "Fake token"})
    # assert response.status_code == 200
    # response = client.get("/organisations/2")
    # assert response.status_code == 200, response.json()
    # response_json = response.json()
    # TODO(jos): make sure Agent is deleted on CASCADE

    body["type"] = "Association"
    response = client.put(f"organisations/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    response = client.get(f"organisations/{identifier}")
    assert response.json()["type"] == "association"

    response = client.delete(f"/organisations/{identifier}", headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()


def test_ai_resource_contacts_field_is_ignored(
        client: TestClient,
        mocked_privileged_token: Mock,
        organisation: Organisation,
        contact: Contact,
        body_agent: dict,
        auto_publish: None,
):
    with DbSession() as session:
        session.add(contact)
        session.commit()
        session.refresh(contact)

    body = copy.copy(body_agent)
    body["contacts"] = [contact.json()]
    response = client.post("/organisations", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/organisations/{identifier}")
    assert response.status_code == 200, response.json()
    assert response.json()["contacts"] == []
