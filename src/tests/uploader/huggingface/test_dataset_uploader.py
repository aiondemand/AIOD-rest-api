from unittest.mock import Mock

import huggingface_hub
import responses
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.ai_asset.ai_asset_table import AIAssetTable
from database.model.dataset.dataset import Dataset
from tests.testutils.paths import path_test_resources


def test_happy_path_new_repository(
    client: TestClient, engine: Engine, mocked_privileged_token: Mock, dataset: Dataset
):
    keycloak_openid.userinfo = mocked_privileged_token
    with Session(engine) as session:
        session.add(dataset)
        session.commit()

    data = {
        "token": "huggingface_token",
        "username": "username",
    }

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
            data=data,
            params={"username": "Fake-username", "token": "Fake-token"},
            headers={"Authorization": "Fake token"},
            files=files,
        )
    assert response.status_code == 200, response.json()
    id_response = response.json()
    assert id_response == 1


def test_repo_already_exists(client: TestClient, engine: Engine, mocked_privileged_token: Mock):
    keycloak_openid.userinfo = mocked_privileged_token
    dataset_id = 1
    with Session(engine) as session:
        session.add_all(
            [
                AIAssetTable(type="dataset"),
                Dataset(
                    identifier=dataset_id,
                    name="Parent",
                    platform="example",
                    platform_identifier="1",
                    description="description text",
                    same_as="",
                ),
            ]
        )
        session.commit()

    data = {
        "token": "huggingface_token",
        "username": "username",
    }

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
            f"/upload/datasets/{dataset_id}/huggingface",
            data=data,
            params={"username": "Fake-username", "token": "Fake-token"},
            headers={"Authorization": "Fake token"},
            files=files,
        )
    assert response.status_code == 200, response.json()
    id_response = response.json()
    assert id_response == dataset_id


# TODO: tests some error handling?
