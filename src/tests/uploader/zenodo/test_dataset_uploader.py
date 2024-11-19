import copy
import responses
import pytest

from datetime import datetime

from unittest.mock import Mock

from fastapi import HTTPException, status
from starlette.testclient import TestClient

from database.model.agent.contact import Contact
from database.model.agent.person import Person

from database.model.platform.platform_names import PlatformName
from database.session import DbSession

from tests.testutils.paths import path_test_resources

import tests.uploader.zenodo.mock_zenodo as zenodo
from uploaders.zenodo_uploader import ZenodoUploader

ENDPOINT = "/upload/datasets/1/zenodo"
FILE1 = "example1.csv"
FILE2 = "example2.tsv"

HEADERS = {"Authorization": "Fake token"}
PARAMS_DRAFT = {"token": "fake-token", "publish": False}
PARAMS_PUBLISH = {"token": "fake-token", "publish": True}


def distribution_from_zenodo(*filenames: str, is_published: bool = False) -> list[dict]:
    files_metadata = (
        zenodo.files_response_from_published(*filenames)["entries"]
        if is_published
        else zenodo.files_response_from_draft(*filenames)
    )
    dist = [
        {
            "platform": "zenodo",
            "platform_resource_identifier": file["file_id" if is_published else "id"],
            "checksum": file["checksum"].split(":")[-1] if is_published else file["checksum"],
            "checksum_algorithm": "md5",
            "content_url": file["links"]["content" if is_published else "download"],
            "content_size_kb": round(file["size" if is_published else "filesize"] / 1000),
            "name": file["key" if is_published else "filename"],
        }
        for file in files_metadata
    ]
    return dist


@pytest.fixture
def db_with_person_and_contact(mocked_privileged_token: Mock, person: Person, contact: Contact):
    with DbSession() as session:
        person.name = "full name"
        person.given_name = "Alice"
        person.surname = "Lewis"
        contact.person = person
        session.add(contact)
        session.commit()


@pytest.fixture
def body_empty(body_asset: dict) -> dict:
    body = copy.deepcopy(body_asset)
    body["platform"] = None
    body["platform_resource_identifier"] = None
    body["license"] = "a-valid-license-id"
    body["distribution"] = []
    body["creator"] = [1]
    return body


@pytest.fixture
def body_no_dist(body_empty: dict) -> dict:
    body = copy.deepcopy(body_empty)
    body["platform"] = "zenodo"
    body["platform_resource_identifier"] = f"zenodo.org:{zenodo.RESOURCE_ID}"
    return body


@pytest.fixture
def body_with_dist(body_no_dist: dict) -> dict:
    body = copy.deepcopy(body_no_dist)
    body["distribution"] = distribution_from_zenodo(FILE1)
    return body


def test_happy_path_creating_repo(
    client: TestClient, body_empty: dict, db_with_person_and_contact: None
):
    """
    Test the successful path for creating a new repository on Zenodo before uploading a file.
    The creation of a new repo must be triggered when platform_resource_identifier is None.
    """
    response = client.post("/datasets/v1", json=body_empty, headers={"Authorization": "Fake token"})
    assert response.status_code == status.HTTP_200_OK, response.json()

    with responses.RequestsMock() as mocked_requests:
        zenodo.mock_create_repo(mocked_requests)
        zenodo.mock_get_licenses(mocked_requests)
        zenodo.mock_upload_file(mocked_requests, FILE1)
        zenodo.mock_get_draft_files(mocked_requests, FILE1)

        with open(path_test_resources() / "contents" / FILE1, "rb") as f:
            test_file = {"file": f}
            response = client.post(ENDPOINT, params=PARAMS_DRAFT, headers=HEADERS, files=test_file)
        assert response.status_code == status.HTTP_200_OK, response.json()
        assert response.json() == 1, response.json()

    response_json = client.get("datasets/v1/1").json()
    assert response_json["platform"] == "zenodo", response_json
    assert (
        response_json["platform_resource_identifier"] == f"zenodo.org:{zenodo.RESOURCE_ID}"
    ), response_json
    assert (
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M") in response_json["aiod_entry"]["date_modified"]
    )
    assert response_json["distribution"] == distribution_from_zenodo(FILE1), response_json


def test_happy_path_existing_repo(
    client: TestClient, body_with_dist: dict, db_with_person_and_contact: None
):
    """
    Test the successful path for an existing repository on Zenodo.
    When the platform_resource_identifier is not None (zenodo.org:int) the code should
    get metadata and url of the existing repo, then upload a file.
    """
    response = client.post(
        "/datasets/v1", json=body_with_dist, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()

    with responses.RequestsMock() as mocked_requests:
        zenodo.mock_get_repo_metadata(mocked_requests)
        zenodo.mock_get_licenses(mocked_requests)
        zenodo.mock_update_metadata(mocked_requests)
        zenodo.mock_upload_file(mocked_requests, FILE1)
        zenodo.mock_get_draft_files(mocked_requests, FILE1)

        with open(path_test_resources() / "contents" / FILE1, "rb") as f:
            test_file = {"file": f}
            response = client.post(ENDPOINT, params=PARAMS_DRAFT, headers=HEADERS, files=test_file)
        assert response.status_code == status.HTTP_200_OK, response.json()
        assert response.json() == 1, response.json()

    response_json = client.get("datasets/v1/1").json()
    assert response_json["platform"] == "zenodo", response_json
    assert (
        response_json["platform_resource_identifier"] == f"zenodo.org:{zenodo.RESOURCE_ID}"
    ), response_json
    assert response_json["distribution"] == distribution_from_zenodo(FILE1), response_json


def test_happy_path_existing_file(
    client: TestClient, body_with_dist: dict, db_with_person_and_contact: None
):
    """
    Test uploading a second file to zenodo.
    """
    response = client.post(
        "/datasets/v1", json=body_with_dist, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()

    with responses.RequestsMock() as mocked_requests:
        zenodo.mock_get_repo_metadata(mocked_requests)
        zenodo.mock_get_licenses(mocked_requests)
        zenodo.mock_update_metadata(mocked_requests)
        zenodo.mock_upload_file(mocked_requests, FILE2)
        zenodo.mock_get_draft_files(mocked_requests, FILE1, FILE2)

        with open(path_test_resources() / "contents" / FILE2, "rb") as f:
            test_file = {"file": f}
            response = client.post(ENDPOINT, params=PARAMS_DRAFT, headers=HEADERS, files=test_file)
        assert response.status_code == status.HTTP_200_OK, response.json()
        assert response.json() == 1, response.json()

    response_json = client.get("datasets/v1/1").json()
    assert response_json["platform"] == "zenodo", response_json
    assert (
        response_json["platform_resource_identifier"] == f"zenodo.org:{zenodo.RESOURCE_ID}"
    ), response_json
    assert response_json["distribution"] == distribution_from_zenodo(
        FILE1
    ) + distribution_from_zenodo(FILE2), response_json


def test_happy_path_updating_an_existing_file(
    client: TestClient, body_with_dist: dict, db_with_person_and_contact: None
):
    """
    Test uploading a second file to zenodo with the same name.
    This must update the existing file.
    """
    updated_file_new_id = "newid000-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

    response = client.post(
        "/datasets/v1", json=body_with_dist, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    with responses.RequestsMock() as mocked_requests:
        zenodo.mock_get_repo_metadata(mocked_requests)
        zenodo.mock_get_licenses(mocked_requests)
        zenodo.mock_update_metadata(mocked_requests)
        zenodo.mock_upload_file(mocked_requests, FILE1)

        draft_response = zenodo.files_response_from_draft(FILE1)
        draft_response[0]["id"] = updated_file_new_id
        mocked_requests.add(
            responses.GET,
            f"{zenodo.BASE_URL}/{zenodo.RESOURCE_ID}/files",
            json=draft_response,
            status=200,
        )

        with open(path_test_resources() / "contents" / FILE1, "rb") as f:
            test_file = {"file": f}
            response = client.post(ENDPOINT, params=PARAMS_DRAFT, headers=HEADERS, files=test_file)
        assert response.status_code == status.HTTP_200_OK, response.json()
        assert response.json() == 1, response.json()

    response_json = client.get("datasets/v1/1").json()
    assert response_json["platform"] == "zenodo", response_json
    assert (
        response_json["platform_resource_identifier"] == f"zenodo.org:{zenodo.RESOURCE_ID}"
    ), response_json
    expected_updated_dist = distribution_from_zenodo(FILE1)
    expected_updated_dist[0]["platform_resource_identifier"] = updated_file_new_id
    assert response_json["distribution"] == expected_updated_dist, response_json


def test_happy_path_publishing(
    client: TestClient, body_empty: dict, db_with_person_and_contact: None
):
    """
    Test publishing the resource on Zenodo after uploading a file.
    The URL of the content should not be empty
    """
    response = client.post("/datasets/v1", json=body_empty, headers={"Authorization": "Fake token"})
    assert response.status_code == status.HTTP_200_OK, response.json()

    with responses.RequestsMock() as mocked_requests:
        zenodo.mock_create_repo(mocked_requests)
        zenodo.mock_get_licenses(mocked_requests)
        zenodo.mock_upload_file(mocked_requests, FILE1)
        zenodo.mock_publish_resource(mocked_requests)
        zenodo.mock_get_published_files(mocked_requests, FILE1)

        with open(path_test_resources() / "contents" / FILE1, "rb") as f:
            test_file = {"file": f}
            response = client.post(
                ENDPOINT, params=PARAMS_PUBLISH, headers=HEADERS, files=test_file
            )
        assert response.status_code == status.HTTP_200_OK, response.json()
        assert response.json() == 1, response.json()

    response_json = client.get("datasets/v1/1").json()
    assert response_json["aiod_entry"]["status"] == "published", response_json
    assert (
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M") in response_json["date_published"]
    ), response_json


def test_attempt_to_upload_published_resource(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_no_dist: dict,
    contact: Contact,
    person: Person,
):
    """
    Test attempt to upload a file to a resource that has already been published.
    This must raise an conflict error 409 and return a message stating
    that the process can't be concluded.
    """
    body = copy.deepcopy(body_no_dist)
    body["distribution"] = distribution_from_zenodo(FILE1, is_published=True)
    body["aiod_entry"]["status"] = "published"

    with DbSession() as session:
        person.name = "Alice Lewis"
        contact.person = person
        session.add(contact)
        session.commit()

    response = client.post("/datasets/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == status.HTTP_200_OK, response.json()

    with responses.RequestsMock() as mocked_requests:
        zenodo.mock_get_repo_metadata(mocked_requests, is_published=True)
        zenodo.mock_get_licenses(mocked_requests)

        with open(path_test_resources() / "contents" / FILE1, "rb") as f:
            test_file = {"file": f}
            response = client.post(
                ENDPOINT, params=PARAMS_PUBLISH, headers=HEADERS, files=test_file
            )

        assert response.status_code == status.HTTP_409_CONFLICT, response.json()
        assert response.json()["detail"] == [
            "This resource is already public and can't be edited with this endpoint. "
            f"You can access and modify it at {zenodo.HTML_URL}/{zenodo.RESOURCE_ID}"
        ], response.json()

    response_json = client.get("datasets/v1/1").json()
    assert response_json["distribution"] == body["distribution"], response_json


def test_platform_name_conflict(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_empty: dict,
    person: Person,
    contact: Contact,
):
    """
    Test error handling on the attempt to upload a dataset with a platform name
    different than zenodo.
    """

    body = copy.deepcopy(body_empty)
    body["platform"] = "huggingface"
    body["platform_resource_identifier"] = "fake-id"

    with DbSession() as session:
        contact.person = person
        session.add(contact)
        session.commit()
    response = client.post("/datasets/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == status.HTTP_200_OK, response.json()

    with responses.RequestsMock() as mocked_request:
        zenodo.mock_get_licenses(mocked_request)
        with open(path_test_resources() / "contents" / FILE1, "rb") as f:
            test_file = {"file": f}
            response = client.post(ENDPOINT, params=PARAMS_DRAFT, headers=HEADERS, files=test_file)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
        assert response.json()["detail"] == (
            "The dataset with identifier 1 should have platform=" f"{PlatformName.zenodo}."
        ), response.json()

    response_json = client.get("datasets/v1/1").json()
    assert response_json["platform"] == "huggingface", response_json
    assert response_json["platform_resource_identifier"] == "fake-id", response_json
    assert response_json["distribution"] == []


def test_fail_due_to_missing_contact_name(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_empty: dict,
    person: Person,
):
    """
    Test to attempt to publish a dataset without creator's name.
    """
    body = copy.deepcopy(body_empty)
    body["creator"] = []

    with DbSession() as session:
        session.add(person)
        session.commit()
    response = client.post("/datasets/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == status.HTTP_200_OK, response.json()

    with responses.RequestsMock():
        with open(path_test_resources() / "contents" / FILE1, "rb") as f:
            test_file = {"file": f}
            response = client.post(
                ENDPOINT, params=PARAMS_PUBLISH, headers=HEADERS, files=test_file
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
        assert response.json()["detail"] == (
            "The dataset must have the name of at least one creator. "
            "Please provide either the person's given name and surname or the organization name. "
            "If given name and surname are not provided, the API will attempt to retrieve the name "
            "from the fields person.name, organization.name, and contact.name, in this order."
        ), response.json()


ERROR_MSG = (
    "The platform_resource_identifier for Zenodo should be "
    "a valid repository identifier or a valid file identifier. "
    "A repository identifier has the following pattern: "
    "the string 'zenodo.org:' followed by an integer: e.g., zenodo.org:100. \n"
    "A file identifier is a string composed by a group of 8 characters, "
    "3 groups of 4 characters, and a group of 12 characters, where the characters "
    "include letters and numbers and the groups are separated by a dash '-': "
    "e.g, abcde123-abcd-0000-ab00-abcdef000000."
)


def test_platform_resource_id_validator():
    """
    Tests if the method `_platform_resource_id_validator` raises a ValueError for an invalid
    value.
    """
    invalid_repo_id = "an/inv@lid|id"
    expected_error = ValueError(ERROR_MSG)

    if expected_error is None:
        ZenodoUploader._platform_resource_id_validator(invalid_repo_id)
    else:
        with pytest.raises(type(expected_error)) as exception_info:
            ZenodoUploader._platform_resource_id_validator(invalid_repo_id)
        assert exception_info.value.args[0] == expected_error.args[0]


MSG_RAISED_TO_CLIENT = (
    f"The platform_resource_identifier is invalid for {PlatformName.zenodo}. " + ERROR_MSG
)

HTTP_EXC = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MSG_RAISED_TO_CLIENT)


@pytest.mark.parametrize(
    "repo_id,expected_error",
    [
        ("zenodo.org:1", None),
        ("zenodo.org:1234567", None),
        ("zenodo.org:02334", HTTP_EXC),
        ("zenodo_org:100", HTTP_EXC),
        ("zenodo.org.100", HTTP_EXC),
        ("zenodo.org.abc", HTTP_EXC),
        ("11111111-9999-0000-1111-123456789012", None),
        ("abcdefgh-abcd-abcd-abcd-abcdefghijkl", None),
        ("abcde123-abcd-0000-ab00-abcdef000000", None),
        ("ABCde123-abcd-0000-ab00-abcdef000000", HTTP_EXC),
        ("abdef123_abcd-0000-ab00-abcdef000000", HTTP_EXC),
        ("abd.0123-abcd-0000-ab00-abcdef000000", HTTP_EXC),
        ("abdef-23-abcd-0000-ab00-abcdef000000", HTTP_EXC),
        ("abcd0123-abcd-0000-ab00-abcdef0000000", HTTP_EXC),
        ("abcd0123-abcd0-0000-ab00-abcdef000000", HTTP_EXC),
        ("abcd0123-abcd-00000-ab00-abcdef000000", HTTP_EXC),
        ("abcd0123-abcd-0000-ab000-abcdef000000", HTTP_EXC),
    ],
)
def test_repo_id(repo_id: str, expected_error: HTTPException | None):
    zenodo_uploader = ZenodoUploader()
    if expected_error is None:
        zenodo_uploader._validate_repo_id(repo_id)
    else:
        with pytest.raises(type(expected_error)) as exception_info:
            zenodo_uploader._validate_repo_id(repo_id)
        assert exception_info.value.status_code == expected_error.status_code
        assert exception_info.value.detail == expected_error.detail
