"""
Test the pricing_info, applies_to, solution, and approach fields on AIAsset
"""

import copy

import pytest
from starlette.testclient import TestClient

from database.model.ai_asset.solution import Solution
from database.model.ai_asset.approach import Approach
from database.session import DbSession
from tests.testutils.users import logged_in_user


def test_pricing_and_applies_fields(
    client: TestClient,
    body_asset: dict,
    auto_publish: None,
):
    """Test that pricing_info and applies_to fields work correctly"""
    # Create a dataset with pricing_info and applies_to
    body = copy.deepcopy(body_asset)
    body["pricing_info"] = "Free for academic use, €50/month for commercial"
    body["applies_to"] = "Computer vision, image classification"

    # Create the dataset
    with logged_in_user():
        response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    dataset_identifier = response.json()["identifier"]

    # Retrieve the dataset and verify fields are present
    response = client.get(f"/datasets/{dataset_identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["pricing_info"] == "Free for academic use, €50/month for commercial"
    assert response_json["applies_to"] == "Computer vision, image classification"

    # Test updating the fields
    body["pricing_info"] = "Free for all users"
    body["applies_to"] = "Natural language processing"

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
    assert response_json["pricing_info"] == "Free for all users"
    assert response_json["applies_to"] == "Natural language processing"


def test_solution_relationship(
    client: TestClient,
    body_asset: dict,
    auto_publish: None,
):
    """Test that solution many-to-many relationship works correctly"""
    # Create solution taxonomy entries
    solution1 = Solution(
        name="machine learning model", definition="A trained ML model", official=True
    )
    solution2 = Solution(
        name="data processing pipeline", definition="Data transformation pipeline", official=True
    )

    with DbSession() as session:
        session.add(solution1)
        session.add(solution2)
        session.commit()
        sol1_name = solution1.name
        sol2_name = solution2.name

    # Create a dataset with solution references
    body = copy.deepcopy(body_asset)
    body["solution"] = [sol1_name, sol2_name]

    with logged_in_user():
        response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    dataset_identifier = response.json()["identifier"]

    # Verify both solutions are linked
    response = client.get(f"/datasets/{dataset_identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert set(response_json["solution"]) == {sol1_name, sol2_name}


def test_approach_relationship(
    client: TestClient,
    body_asset: dict,
    auto_publish: None,
):
    """Test that approach many-to-many relationship works correctly"""
    # Create approach taxonomy entries
    approach1 = Approach(
        name="supervised learning", definition="Learning with labeled data", official=True
    )
    approach2 = Approach(
        name="deep learning", definition="Neural network based learning", official=True
    )

    with DbSession() as session:
        session.add(approach1)
        session.add(approach2)
        session.commit()
        app1_name = approach1.name
        app2_name = approach2.name

    # Create a dataset with approach references
    body = copy.deepcopy(body_asset)
    body["approach"] = [app1_name, app2_name]

    with logged_in_user():
        response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    dataset_identifier = response.json()["identifier"]

    # Verify both approaches are linked
    response = client.get(f"/datasets/{dataset_identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert set(response_json["approach"]) == {app1_name, app2_name}


def test_all_fields_together(
    client: TestClient,
    body_asset: dict,
    auto_publish: None,
):
    """Test using pricing_info, applies_to, solution, and approach together"""
    # Create taxonomy entries
    solution = Solution(
        name="classification model", definition="A model for classification", official=True
    )
    approach = Approach(
        name="transfer learning", definition="Using pretrained models", official=True
    )

    with DbSession() as session:
        session.add(solution)
        session.add(approach)
        session.commit()
        sol_name = solution.name
        app_name = approach.name

    # Create a dataset with all fields populated
    body = copy.deepcopy(body_asset)
    body["pricing_info"] = "€100/month"
    body["applies_to"] = "Image classification tasks"
    body["solution"] = [sol_name]
    body["approach"] = [app_name]

    with logged_in_user():
        response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    dataset_identifier = response.json()["identifier"]

    # Verify all fields
    response = client.get(f"/datasets/{dataset_identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["pricing_info"] == "€100/month"
    assert response_json["applies_to"] == "Image classification tasks"
    assert response_json["solution"] == [sol_name]
    assert response_json["approach"] == [app_name]
