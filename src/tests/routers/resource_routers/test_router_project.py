import copy
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.session import DbSession
from tests.testutils.users import logged_in_user
from versioning import Version


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_resource: dict,
    person: Person,
    organisation: Organisation,
    publication: Publication,
    dataset: Dataset,
    auto_publish: None,
):
    with DbSession() as session:
        session.add(person)
        session.merge(organisation)
        session.merge(dataset)
        session.merge(publication)
        session.commit()
        session.refresh(person)

    body = copy.deepcopy(body_resource)
    body["start_date"] = "2021-02-02T15:15:00"
    body["end_date"] = "2021-02-03T15:15:00"
    body["total_cost_euros"] = 10000000.53
    body["funder"] = [organisation.identifier]
    body["participant"] = [organisation.identifier]
    body["coordinator"] = organisation.identifier
    body["produced"] = [dataset.identifier]
    body["used"] = [publication.identifier]

    response = client.post("/projects", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/projects/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["start_date"] == "2021-02-02T15:15:00"
    assert response_json["end_date"] == "2021-02-03T15:15:00"
    assert response_json["total_cost_euros"] == 10000000.53
    assert response_json["funder"] == [organisation.identifier]
    assert response_json["participant"] == [organisation.identifier]
    assert response_json["coordinator"] == organisation.identifier
    assert response_json["produced"] == [dataset.identifier]
    assert response_json["used"] == [publication.identifier]

    # Cleanup, so that all resources can be deleted in the teardown
    body["funder"] = []
    body["participant"] = []
    body["coordinator"] = None
    body["produced"] = []
    body["used"] = []
    response = client.put(f"/projects/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()


@pytest.mark.versions(Version.V2)
@pytest.mark.parametrize(
    "field_alias", ["total_cost_euro", "total_cost_euros"]
)
def test_happy_path_v2_total_cost_euros(
        client: TestClient,
        field_alias: str,
        body_resource: dict,
        auto_publish: None,
):
    body = copy.deepcopy(body_resource)
    body[field_alias] = 10000000.53

    with logged_in_user():
        response = client.post("/projects", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/projects/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["total_cost_euros"] == 10000000.53
    assert response_json["total_cost_euro"] == 10000000.53
