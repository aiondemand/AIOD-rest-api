import copy
from unittest.mock import Mock

from starlette.testclient import TestClient

from database.model.agent.person import Person
from database.session import DbSession


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_resource: dict,
    person: Person,
    auto_publish: None,
):

    with DbSession() as session:
        session.add(person)
        session.commit()
        session.refresh(person)

    body = copy.copy(body_resource)
    body["start_date"] = "2021-02-03T15:15:00"
    body["end_date"] = "2022-02-03T15:15:00"
    body["schedule"] = "Some text"
    body["registration_link"] = "https://example.com/registration-form"
    body["performer"] = [person.identifier]
    body["organiser"] = person.identifier
    body["status"] = "scheduled"
    body["mode"] = "offline"
    locations = [
        {
            "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
        },
        {
            "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
        },
    ]
    body["location"] = locations
    body["content"] = {"plain": "plain content"}

    response = client.post("/events", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/events/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["start_date"] == "2021-02-03T15:15:00"
    assert response_json["end_date"] == "2022-02-03T15:15:00"
    assert response_json["schedule"] == "Some text"
    assert response_json["registration_link"] == "https://example.com/registration-form"
    assert response_json["performer"] == [person.identifier]
    assert response_json["organiser"] == person.identifier
    assert response_json["status"] == "scheduled"
    assert response_json["mode"] == "offline"
    assert response_json["location"] == locations
    assert response_json["content"] == {"plain": "plain content"}

    # Cleanup, so that all resources can be deleted in the teardown
    body["performer"] = []
    body["organiser"] = None
    response = client.put(f"/events/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
