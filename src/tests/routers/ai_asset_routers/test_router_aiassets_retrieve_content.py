import copy
import pytest
import responses

from pytest import FixtureRequest
from unittest.mock import Mock

from fastapi import status
from sqlalchemy.engine import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.person import Person
from tests.testutils.paths import path_test_resources


TEST_URL1 = "https://www.example.com/example1.csv/content"
TEST_URL2 = "https://www.example.com/example2.tsv/content"

SAMPLE_RESOURCE_NAME = "datasets"
SAMPLE_ENDPOINT = f"{SAMPLE_RESOURCE_NAME}/v1/1/content"


def mock_response1(mocked_requests: responses.RequestsMock):
    with open(
        path_test_resources() / "contents" / "example1.csv",
        "r",
    ) as f:
        csv_data = f.read()

    mocked_requests.add(
        responses.GET,
        TEST_URL1,
        body=csv_data,
        status=200,
    )


def mock_response2(mocked_requests: responses.RequestsMock):
    with open(
        path_test_resources() / "contents" / "example2.tsv",
        "r",
    ) as f:
        csv_data = f.read()
    mocked_requests.add(
        responses.GET,
        TEST_URL2,
        body=csv_data,
        status=200,
    )


def set_up(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body: dict,
    person: Person,
    resource_name: str,
):
    """
    Set up the test environment for API endpoint testing.
    This function prepares the test environment by mocking user info,
    adding a person to the database, and sending a POST request to the
    specified endpoint for the given resource.
    """
    keycloak_openid.userinfo = mocked_privileged_token
    with Session(engine) as session:
        session.add(person)
        session.commit()

    response = client.post(
        f"/{resource_name}/v1", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()


@pytest.fixture(params=["datasets", "case_studies", "experiments", "ml_models", "publications"])
def resource_name(request: FixtureRequest) -> str:
    return request.param


def test_ai_asset_has_endopoints(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset_with_single_distribution: dict,
    person: Person,
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
    set_up(client, engine, mocked_privileged_token, body, person, resource_name)

    default_endpoint = f"{resource_name}/v1/1/content"

    with responses.RequestsMock() as mocked_requests:
        mock_response1(mocked_requests)

        response = client.get(default_endpoint)
        assert response.status_code == status.HTTP_200_OK, response.json()
        response0 = client.get(default_endpoint + "/0")
        assert response0.status_code == status.HTTP_200_OK, response0.json()


def test_endpoints_when_empty_distribution(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset: dict,
    person: Person,
):
    """
    Test retrieving content from an AIAsset with an empty distribution list.

    This test case checks the behavior of the API when attempting to retrieve content
    from an AIAsset with no distributions. It verifies that the correct HTTP status
    and error details are returned.
    """
    body = copy.deepcopy(body_asset)
    body["distribution"] = []
    set_up(client, engine, mocked_privileged_token, body, person, SAMPLE_RESOURCE_NAME)

    response = client.get(SAMPLE_ENDPOINT)
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()
    assert response.json()["detail"] == "Distribution not found.", response.json()

    response0 = client.get(SAMPLE_ENDPOINT + "/0")
    assert response0.status_code == status.HTTP_404_NOT_FOUND, response0.json()
    assert response0.json()["detail"] == "Distribution not found.", response0.json()


@pytest.fixture
def body_asset_with_single_distribution(body_asset: dict) -> dict:
    body = copy.deepcopy(body_asset)
    body["distribution"][0]["content_url"] = TEST_URL1
    body["distribution"][0]["encoding_format"] = "text/csv"
    body["distribution"][0]["name"] = "example1.csv"
    return body


def test_endpoints_when_single_distribution(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset_with_single_distribution: dict,
    person: Person,
):
    """
    Test retrieving content from an AIAsset with a single distribution.

    This test case checks the behavior of the API when attempting to retrieve content
    from an AIAsset with single distribution. It verifies that the correct HTTP status,
    content, headers, and filename are returned.
    """
    body = copy.deepcopy(body_asset_with_single_distribution)
    set_up(client, engine, mocked_privileged_token, body, person, SAMPLE_RESOURCE_NAME)

    with responses.RequestsMock() as mocked_requests:
        mock_response1(mocked_requests)

        response = client.get(SAMPLE_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, response.json()
        assert str(response.content, encoding="utf-8") == "row1,row2,row3\n1,2,3", response.content
        assert (
            response.headers.get("Content-Disposition") == "attachment; filename=example1.csv"
        ), response.headers
        assert response.headers.get("Content-Type") == "text/csv", response.headers

        response0 = client.get(SAMPLE_ENDPOINT + "/0")
        assert response0.status_code == status.HTTP_200_OK, response0.json()
        assert (
            str(response0.content, encoding="utf-8") == "row1,row2,row3\n1,2,3"
        ), response0.content

        response1 = client.get(SAMPLE_ENDPOINT + "/1")
        assert response1.status_code == status.HTTP_400_BAD_REQUEST, response1.json()
        assert response1.json()["detail"] == "Distribution index out of range.", response1.json()

        response2 = client.get(SAMPLE_ENDPOINT + "/-1")
        assert response2.status_code == status.HTTP_200_OK, response2.json()
        assert (
            str(response2.content, encoding="utf-8") == "row1,row2,row3\n1,2,3"
        ), response2.content


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
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset_with_two_distributions: dict,
    person: Person,
):
    """
    Test getting content from an AIAsset with multiple distributions.

    This test case checks the behavior of the API when attempting to retrieve content
    from an AIAsset with two distribution. It verifies that the correct HTTP status,
    content, headers, and filename are returned.
    """
    body = copy.deepcopy(body_asset_with_two_distributions)
    set_up(client, engine, mocked_privileged_token, body, person, SAMPLE_RESOURCE_NAME)

    with responses.RequestsMock() as mocked_requests:
        mock_response1(mocked_requests)
        mock_response2(mocked_requests)

        response = client.get(SAMPLE_ENDPOINT)
        assert response.status_code == status.HTTP_409_CONFLICT, response.json()
        assert response.json()["detail"] == [
            "Multiple distributions encountered. "
            "Use another endpoint indicating the distribution index `distribution_idx` "
            "at the end of the url for a especific distribution."
        ], response.json()

        response0 = client.get(SAMPLE_ENDPOINT + "/0")
        assert response0.status_code == status.HTTP_200_OK, response0.json()
        assert (
            str(response0.content, encoding="utf-8") == "row1,row2,row3\n1,2,3"
        ), response0.content
        assert (
            response0.headers.get("Content-Disposition") == "attachment; filename=example1.csv"
        ), response0.headers
        assert response0.headers.get("Content-Type") == "text/csv", response0.headers

        response1 = client.get(SAMPLE_ENDPOINT + "/1")
        assert response1.status_code == status.HTTP_200_OK, response1.json()
        assert (
            str(response1.content, encoding="utf-8") == "col1;col2;col3\n1;2;3"
        ), response1.content


@pytest.fixture(params=["", None])
def filename(request: FixtureRequest) -> str:
    return request.param


@pytest.fixture(params=["", None])
def encoding_format(request: FixtureRequest) -> str:
    return request.param


def test_headers_when_distribution_has_missing_fields(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset_with_single_distribution: dict,
    person: Person,
    filename: str,
    encoding_format: str,
):
    """
    Test response headers from an AIAsset with a distribution with missing
    filename and/or encoding format.

    The headers should be filled with the last part of the url in case the filename is missing
    in the distribution. On the other hand, the encoding format should be filled with "unknown".
    """
    body = copy.deepcopy(body_asset_with_single_distribution)
    body["distribution"][0]["name"] = filename
    body["distribution"][0]["encoding_format"] = encoding_format

    alternate_filename = body["distribution"][0]["content_url"].split("/")[-1]

    set_up(client, engine, mocked_privileged_token, body, person, SAMPLE_RESOURCE_NAME)

    with responses.RequestsMock() as mocked_requests:
        mock_response1(mocked_requests)

        response = client.get(SAMPLE_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, response.json()
        assert (
            response.headers.get("Content-Disposition")
            == f"attachment; filename={alternate_filename}"
        ), response.headers
        assert "content-type" not in response.headers.keys(), response.headers

        response0 = client.get(SAMPLE_ENDPOINT + "/0")
        assert response0.status_code == status.HTTP_200_OK, response0.json()
        assert (
            response0.headers.get("Content-Disposition")
            == f"attachment; filename={alternate_filename}"
        ), response0.headers
        assert "content-type" not in response0.headers.keys(), response0.headers
