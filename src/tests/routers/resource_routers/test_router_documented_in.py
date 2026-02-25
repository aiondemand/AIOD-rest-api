"""
Test the documented_in relationship on AIResource
"""

import copy

import pytest
from starlette.testclient import TestClient

from database.model.knowledge_asset.publication import Publication
from database.model.dataset.dataset import Dataset
from database.session import DbSession
from tests.testutils.users import logged_in_user


def test_documented_in_relationship(
    client: TestClient,
    body_asset: dict,
    publication: Publication,
    auto_publish: None,
):
    """Test that documented_in field correctly links to KnowledgeAssets (Publications)"""
    publication_identifier = publication.identifier

    # Add publication to the database
    with DbSession() as session:
        session.merge(publication)
        session.commit()

    # Create a dataset with documented_in reference
    body = copy.deepcopy(body_asset)
    body["documented_in"] = [publication_identifier]

    # Create the dataset
    with logged_in_user():
        response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    dataset_identifier = response.json()["identifier"]

    # Retrieve the dataset and verify documented_in is present
    response = client.get(f"/datasets/{dataset_identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert "documented_in" in response_json
    assert response_json["documented_in"] == [publication_identifier]

    # Test updating documented_in
    body["documented_in"] = []
    with logged_in_user():
        response = client.put(
            f"/datasets/{dataset_identifier}",
            json=body,
            headers={"Authorization": "Fake token"},
        )
    assert response.status_code == 200, response.json()

    # Verify the update
    response = client.get(f"/datasets/{dataset_identifier}")
    response_json = response.json()
    assert response_json["documented_in"] == []


def test_documented_in_multiple_publications(
    client: TestClient,
    body_asset: dict,
    publication_factory,
    auto_publish: None,
):
    """Test that documented_in can reference multiple publications"""
    # Create two publications
    pub1 = publication_factory()
    pub2 = publication_factory()

    with DbSession() as session:
        session.add(pub1)
        session.add(pub2)
        session.commit()
        pub1_id = pub1.identifier
        pub2_id = pub2.identifier

    # Create dataset with both publications
    body = copy.deepcopy(body_asset)
    body["documented_in"] = [pub1_id, pub2_id]

    with logged_in_user():
        response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    dataset_identifier = response.json()["identifier"]

    # Verify both publications are linked
    response = client.get(f"/datasets/{dataset_identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert set(response_json["documented_in"]) == {pub1_id, pub2_id}
