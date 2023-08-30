import copy
from unittest.mock import Mock

from sqlalchemy.engine import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication


def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_resource: dict,
    person: Person,
    organisation: Organisation,
    publication: Publication,
    dataset: Dataset,
):
    keycloak_openid.userinfo = mocked_privileged_token

    with Session(engine) as session:
        session.add(person)
        session.merge(organisation)
        session.merge(dataset)
        session.merge(publication)
        session.commit()

    body = copy.deepcopy(body_resource)
    body["start_date"] = "2021-02-02T15:15:00"
    body["end_date"] = "2021-02-03T15:15:00"
    body["total_cost_euro"] = 10000000.53
    body["funder"] = [1]
    body["participant"] = [1]
    body["coordinator"] = 1
    body["produced"] = [1]  # the dataset
    body["used"] = [2]  # the publication

    response = client.post("/projects/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/projects/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["start_date"] == "2021-02-02T15:15:00"
    assert response_json["end_date"] == "2021-02-03T15:15:00"
    assert response_json["total_cost_euro"] == 10000000.53
    assert response_json["funder"] == [1]
    assert response_json["participant"] == [1]
    assert response_json["coordinator"] == 1
    assert response_json["produced"] == [1]  # the dataset
    assert response_json["used"] == [2]  # the publication
