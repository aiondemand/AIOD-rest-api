import copy
from unittest.mock import Mock

import pytest
from fastapi import status
from pytest import FixtureRequest
from starlette.testclient import TestClient

from database.model.agent.person import Person
from database.session import DbSession

TEST_URL1 = "https://www.example.com/example1.csv/content"
TEST_URL2 = "https://www.example.com/example2.tsv/content"

SAMPLE_RESOURCE_NAME = "datasets"
SAMPLE_ENDPOINT = f"{SAMPLE_RESOURCE_NAME}/v1/1/content"


@pytest.fixture
def db_with_person(person: Person, mocked_privileged_token: Mock) -> None:
    with DbSession() as session:
        session.add(person)
        session.commit()


@pytest.fixture(params=["datasets", "case_studies", "experiments", "ml_models", "publications"])
def resource_name(request: FixtureRequest) -> str:
    return request.param


def test_ai_asset_has_endpoints(
    client: TestClient,
    body_asset_with_single_distribution: dict,
    db_with_person: None,
    resource_name: str,
):
    """
    Test the existence and functionality of endpoints for an AIAsset resource.

    It uses a mocked request and asserts the success requests to the endpoints:
        + "{resource_name}/v1/1/content"
        + f"{resource_name}/v1/1/content/0"
    return a response with status code 200.
    """
    body = copy.deepcopy(body_asset_with_single_distribution)
    response = client.post(
        f"/{resource_name}/v1", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()

    default_endpoint = f"{resource_name}/v1/1/content"

    response = client.get(default_endpoint, allow_redirects=False)
    assert response.status_code == status.HTTP_303_SEE_OTHER, response.status_code
    response0 = client.get(default_endpoint + "/0", allow_redirects=False)
    assert response0.status_code == status.HTTP_303_SEE_OTHER, response0.status_code


def test_endpoints_when_empty_distribution(
    client: TestClient,
    body_asset: dict,
    db_with_person: None,
):
    """
    Test retrieving content from an AIAsset with an empty distribution list.

    This test case checks the behavior of the API when attempting to retrieve content
    from an AIAsset with no distributions. It verifies that the correct HTTP status
    and error details are returned.
    """
    body = copy.deepcopy(body_asset)
    body["distribution"] = []

    response = client.post(
        f"/{SAMPLE_RESOURCE_NAME}/v1", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()

    response = client.get(SAMPLE_ENDPOINT, allow_redirects=False)
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.content
    assert response.json()["detail"] == "Distribution not found.", response.content

    response0 = client.get(SAMPLE_ENDPOINT + "/0", allow_redirects=False)
    assert response0.status_code == status.HTTP_404_NOT_FOUND, response0.content
    assert response0.json()["detail"] == "Distribution not found.", response0.content


@pytest.fixture
def body_asset_with_single_distribution(body_asset: dict) -> dict:
    body = copy.deepcopy(body_asset)
    body["distribution"][0]["content_url"] = TEST_URL1
    body["distribution"][0]["encoding_format"] = "text/csv"
    body["distribution"][0]["name"] = "example1.csv"
    return body


def test_endpoints_when_single_distribution(
    client: TestClient,
    body_asset_with_single_distribution: dict,
    db_with_person: None,
):
    """
    Test retrieving content from an AIAsset with a single distribution.

    This test case checks the behavior of the API when attempting to retrieve content
    from an AIAsset with single distribution. It verifies that the correct HTTP status,
    content, and headers are returned.
    """
    body = copy.deepcopy(body_asset_with_single_distribution)
    response = client.post(
        f"/{SAMPLE_RESOURCE_NAME}/v1", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()

    response = client.get(SAMPLE_ENDPOINT, allow_redirects=False)
    assert response.status_code == status.HTTP_303_SEE_OTHER, response.content
    headers = response.headers
    assert headers["location"] == TEST_URL1, headers

    response0 = client.get(SAMPLE_ENDPOINT + "/0", allow_redirects=False)
    assert response0.status_code == status.HTTP_303_SEE_OTHER, response0.content
    headers0 = response.headers
    assert headers0["location"] == TEST_URL1, headers0

    response1 = client.get(SAMPLE_ENDPOINT + "/1", allow_redirects=False)
    assert response1.status_code == status.HTTP_400_BAD_REQUEST, response1.content

    response2 = client.get(SAMPLE_ENDPOINT + "/-1", allow_redirects=False)
    assert response2.status_code == status.HTTP_303_SEE_OTHER, response2.content


@pytest.fixture
def body_asset_with_two_distributions(body_asset_with_single_distribution: dict) -> dict:
    body = copy.deepcopy(body_asset_with_single_distribution)
    distribution = copy.deepcopy(body["distribution"][0])
    body["distribution"].append(distribution)
    body["distribution"][1]["content_url"] = TEST_URL2
    body["distribution"][1]["encoding_format"] = "text/tsv"
    body["distribution"][1]["name"] = "example2.tsv"
    return body


def test_endpoints_when_two_distributions(
    client: TestClient,
    body_asset_with_two_distributions: dict,
    db_with_person: None,
):
    """
    Test getting content from an AIAsset with multiple distributions.

    This test case checks the behavior of the API when attempting to retrieve content
    from an AIAsset with two distribution. It verifies that the correct HTTP status,
    content, and headers are returned.
    """
    body = copy.deepcopy(body_asset_with_two_distributions)
    response = client.post(
        f"/{SAMPLE_RESOURCE_NAME}/v1", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()

    response = client.get(SAMPLE_ENDPOINT, allow_redirects=False)
    assert response.status_code == status.HTTP_409_CONFLICT, response.content
    assert response.json()["detail"] == [
        "Multiple distributions encountered. "
        "Use another endpoint indicating the distribution index `distribution_idx` "
        "at the end of the url for a specific distribution."
    ], response.content

    response0 = client.get(SAMPLE_ENDPOINT + "/0", allow_redirects=False)
    assert response0.status_code == status.HTTP_303_SEE_OTHER, response0.content
    headers0 = response0.headers
    assert headers0["location"] == TEST_URL1, headers0

    response1 = client.get(SAMPLE_ENDPOINT + "/1", allow_redirects=False)
    headers1 = response1.headers
    assert response1.status_code == status.HTTP_303_SEE_OTHER, response1.content
    assert headers1["location"] == TEST_URL2, headers1
