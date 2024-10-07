import copy
from unittest.mock import Mock
from fastapi import HTTPException

import huggingface_hub
import pytest
import responses
from starlette import status
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.dataset.dataset import Dataset
from database.model.platform.platform_names import PlatformName
from database.session import DbSession
from tests.testutils.paths import path_test_resources
from uploaders.hugging_face_uploader import HuggingfaceUploader


def test_happy_path_new_repository(
    client: TestClient, mocked_privileged_token: Mock, dataset: Dataset
):
    dataset = copy.deepcopy(dataset)
    dataset.platform = "huggingface"
    dataset.platform_resource_identifier = "Fake-username/test"

    keycloak_openid.introspect = mocked_privileged_token
    with DbSession() as session:
        session.add(dataset)
        session.commit()

    with open(path_test_resources() / "uploaders" / "huggingface" / "example.csv", "rb") as f:
        files = {"file": f.read()}

    with responses.RequestsMock() as mocked_requests:
        mocked_requests.add(
            responses.POST,
            "https://huggingface.co/api/repos/create",
            json={"url": "url"},
            status=200,
        )
        huggingface_hub.upload_file = Mock(return_value=None)
        response = client.post(
            "/upload/datasets/1/huggingface",
            params={"username": "Fake-username", "token": "Fake-token"},
            headers={"Authorization": "Fake token"},
            files=files,
        )

        assert response.status_code == 200, response.json()
        id_response = response.json()
        assert id_response == 1


def test_happy_path_generating_repo_id(
    client: TestClient, mocked_privileged_token: Mock, dataset: Dataset
):
    dataset = copy.deepcopy(dataset)
    dataset.platform = None
    dataset.platform_resource_identifier = None
    dataset.name = "Repo Test Name 1"

    keycloak_openid.introspect = mocked_privileged_token
    with DbSession() as session:
        session.add(dataset)
        session.commit()

    with open(path_test_resources() / "uploaders" / "huggingface" / "example.csv", "rb") as f:
        files = {"file": f.read()}

    with responses.RequestsMock() as mocked_requests:
        mocked_requests.add(
            responses.POST,
            "https://huggingface.co/api/repos/create",
            json={"url": "url"},
            status=200,
        )
        huggingface_hub.upload_file = Mock(return_value=None)
        response = client.post(
            "/upload/datasets/1/huggingface",
            params={"username": "Fake-username", "token": "Fake-token"},
            headers={"Authorization": "Fake token"},
            files=files,
        )

        assert response.status_code == 200, response.json()
        id_response = response.json()
        assert id_response == 1


def test_failed_generating_repo_id(
    client: TestClient, mocked_privileged_token: Mock, dataset: Dataset
):
    dataset = copy.deepcopy(dataset)
    dataset.platform = None
    dataset.platform_resource_identifier = None
    dataset.name = "Repo inv@lid name"

    keycloak_openid.introspect = mocked_privileged_token
    with DbSession() as session:
        session.add(dataset)
        session.commit()

    with open(path_test_resources() / "uploaders" / "huggingface" / "example.csv", "rb") as f:
        files = {"file": f.read()}

    huggingface_hub.upload_file = Mock(return_value=None)
    response = client.post(
        "/upload/datasets/1/huggingface",
        params={"username": "Fake-username", "token": "Fake-token"},
        headers={"Authorization": "Fake token"},
        files=files,
    )

    assert response.status_code == 400, response.json()
    error_msg = response.json()["detail"]
    assert (
        "We derived an invalid HuggingFace identifier: Fake-username/Repo_inv@lid_name" in error_msg
    )


def test_repo_already_exists(client: TestClient, mocked_privileged_token: Mock, dataset: Dataset):
    keycloak_openid.userinfo = mocked_privileged_token

    dataset = copy.deepcopy(dataset)
    dataset.platform = "huggingface"
    dataset.platform_resource_identifier = "Fake-username/test"

    with DbSession() as session:
        session.add(dataset)
        session.commit()

    with open(path_test_resources() / "uploaders" / "huggingface" / "example.csv", "rb") as f:
        files = {"file": f.read()}

    with responses.RequestsMock() as mocked_requests:
        mocked_requests.add(
            responses.POST,
            "https://huggingface.co/api/repos/create",
            json={
                "error": "You already created this dataset repo",
                "url": "url",
            },
            status=409,
        )
        huggingface_hub.upload_file = Mock(return_value=None)
        response = client.post(
            "/upload/datasets/1/huggingface",
            params={"username": "Fake-username", "token": "Fake-token"},
            headers={"Authorization": "Fake token"},
            files=files,
        )
        assert response.status_code == 200, response.json()
        id_response = response.json()
        assert id_response == 1


def test_wrong_platform(client: TestClient, mocked_privileged_token: Mock, dataset: Dataset):
    keycloak_openid.userinfo = mocked_privileged_token

    dataset = copy.deepcopy(dataset)
    dataset.platform = "example"
    dataset.platform_resource_identifier = "Fake-username/test"

    with DbSession() as session:
        session.add(dataset)
        session.commit()

    with open(path_test_resources() / "uploaders" / "huggingface" / "example.csv", "rb") as f:
        files = {"file": f.read()}

    response = client.post(
        "/upload/datasets/1/huggingface",
        params={"username": "Fake-username", "token": "Fake-token"},
        headers={"Authorization": "Fake token"},
        files=files,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
    assert (
        response.json()["detail"]
        == "The dataset with identifier 1 should have platform=PlatformName.huggingface."
    )


ERROR_MSG_PREFIX = f"The platform_resource_identifier is invalid for {PlatformName.huggingface}. "


@pytest.mark.parametrize(
    "username,dataset_name,expected_error",
    [
        ("0-hero", "0-hero/OIG-small-chip2", None),
        ("user", "user/Foo-BAR_foo.bar123", None),
        (
            "user",
            "user/Test name with ?",
            HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    ERROR_MSG_PREFIX
                    + "Repo id must use alphanumeric chars or '-', '_', '.', '--' and '..' are "
                    "forbidden, '-' and '.' cannot start or end the name, max length is 96: "
                    "'user/Test name with ?'."
                ),
            ),
        ),
        (
            "username",
            "acronym_identification",
            HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    ERROR_MSG_PREFIX
                    + "The username should be part of the platform_resource_identifier "
                    "for HuggingFace: username/acronym_identification. Please update the dataset "
                    "platform_resource_identifier."
                ),
            ),
        ),
        (
            "user",
            "user/data/set",
            HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    ERROR_MSG_PREFIX
                    + "Repo id must be in the form 'repo_name' or 'namespace/repo_name': "
                    "'user/data/set'. Use `repo_type` argument if needed."
                ),
            ),
        ),
        (
            "user",
            "wrong-namespace/name",
            HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    ERROR_MSG_PREFIX
                    + "The namespace (the first part of the platform_resource_identifier) "
                    "should be equal to the username, but wrong-namespace != user."
                ),
            ),
        ),
        (
            "user",
            "user/" + "a" * 200,
            HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    ERROR_MSG_PREFIX
                    + "Repo id must use alphanumeric chars or '-', '_', '.', '--' and '..' are "
                    "forbidden, '-' and '.' cannot start or end the name, max length is 96: "
                    "'user/" + "a" * 200 + "'."
                ),
            ),
        ),
    ],
)
def test_validate_repo_id(username: str, dataset_name: str, expected_error: HTTPException | None):
    huggingface_uploader = HuggingfaceUploader()
    if expected_error is None:
        huggingface_uploader._validate_repo_id(dataset_name, username)
    else:
        with pytest.raises(type(expected_error)) as exception_info:
            huggingface_uploader._validate_repo_id(dataset_name, username)

        assert exception_info.value.status_code == expected_error.status_code
        assert exception_info.value.detail == expected_error.detail
