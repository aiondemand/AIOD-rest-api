import io
from http import HTTPStatus

import pytest
from fastapi.encoders import jsonable_encoder
from starlette.testclient import TestClient

from tests.testutils.users import logged_in_user, register_asset
from routers.resource_routers.organisation_router import ALLOWED_IMAGE_TYPES


@pytest.fixture(params=[
    "organisation", "project",
])
def resource_pair(request):
    resource_name = request.param
    resource = request.getfixturevalue(request.param)
    return resource_name, resource


def test_post_image(
    client: TestClient,
    resource_pair
    ):
    name, resource = resource_pair
    identifier = register_asset(resource)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    with logged_in_user():
        response = client.post(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )
    assert response.status_code == HTTPStatus.OK, response.json()

def test_post_image_too_large(
    client: TestClient,
    resource_pair
    ):
    name, resource = resource_pair
    identifier = register_asset(resource)

    large_content = b"x" * (1 * 1024 * 1024 + 1)
    large_image = io.BytesIO(large_content)
    large_image.name = "big_logo.png"

    with logged_in_user():
        response = client.post(
            f"/{name}s/{identifier}/image",
            params={"name": "big_logo"},
            files={"file": ("big_logo.png", large_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )

    assert response.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    assert response.json()["detail"] == "File too large (max 1MB)."


def test_post_image_incorrect_type(client: TestClient, resource_pair):
    name, resource = resource_pair
    identifier = register_asset(resource)
    pdf_data = io.BytesIO(b"%PDF-1.4 test-pdf content")

    with logged_in_user():
        response = client.post(
            f"/{name}s/{identifier}/image",
            params={"name": "wrong_logo_type"},
            files={"file": ("wrong_logo_type.pdf", pdf_data, "application/pdf")},
            headers={"Authorization": "Fake token"},
        )

    assert response.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert response.json()["detail"] == f"Unsupported file type application/pdf. Allowed image types: {ALLOWED_IMAGE_TYPES}."


def test_put_image(
        client: TestClient,
        resource_pair,
    ):
    name, resource = resource_pair
    identifier = register_asset(resource)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    with logged_in_user():
        response = client.post(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )

        response = client.put(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )

        assert response.status_code == HTTPStatus.OK, response.json()

def test_put_image_non_existent(
        client: TestClient,
        resource_pair
    ):
    name, resource = resource_pair
    identifier = register_asset(resource)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    with logged_in_user():

        response = client.put(
            f"/{name}s/{identifier}/image",
            params={"name": "LOGO"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["detail"] == "No image with the name 'LOGO' found in the database."


@pytest.mark.parametrize("get_image", [False, True])
def test_get_with_and_without_image(client: TestClient, resource_pair, get_image: bool):
    name, resource = resource_pair
    identifier = register_asset(resource)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    with logged_in_user():
        response = client.post(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )

    assert response.status_code == HTTPStatus.OK, response.json()

    response = client.get(f"/{name}s/{identifier}?get_image={str(get_image).lower()}")
    assert response.status_code == HTTPStatus.OK

    response = response.json()

    if get_image:
        assert response["media"][1]["binary_blob"]
    else:
        assert not response["media"][1].get("binary_blob")

    assert response["media"][1]["name"] == "logo"
    assert response["media"][1]["encoding_format"] == "image/png"


def test_get_image(
        client: TestClient,
        resource_pair,
    ):
    name, resource = resource_pair
    identifier = register_asset(resource)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")

    with logged_in_user():
        response = client.post(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )


    response = client.get(
        f"/{name}s/{identifier}/image"
    )
    assert response.status_code == HTTPStatus.OK
    response = response.json()
    assert response[0]["binary_blob"]
    assert response[0]["name"] == "logo"
    assert response[0]["encoding_format"] == "image/png"


def test_get_image_non_existent(
        client: TestClient,
        resource_pair,
    ):
    name, resource = resource_pair
    identifier = register_asset(resource)
    response = client.get(
        f"/{name}s/{identifier}/image"
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


def test_delete_image(
        client: TestClient,
        resource_pair
    ):
    name, resource = resource_pair
    identifier = register_asset(resource)
    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")

    with logged_in_user():
        response = client.post(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )

        response = client.delete(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK

        second_delete_response = client.delete(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            headers={"Authorization": "Fake token"},
        )
        assert second_delete_response.status_code == HTTPStatus.NOT_FOUND
        assert "No image with the name" in second_delete_response.json()["detail"]


def test_put_without_media_keeps_media(
        client: TestClient,
        resource_pair
):
    name, resource = resource_pair
    resource.media = []
    identifier = register_asset(resource)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    with logged_in_user():
        response = client.post(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

        resource.name = "new name"
        response = client.put(
            f"/{name}s/{identifier}",
            json=jsonable_encoder(resource.dict()),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()
        response = client.get(
            f"/{name}s/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()
        assert response.json()["name"] == "new name", response.json()
        assert response.json()["media"], response.json()


def test_put_with_media_keeps_media_if_no_new_binary(
        client: TestClient,
        resource_pair
):
    name, resource = resource_pair
    resource.media = []
    identifier = register_asset(resource)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    with logged_in_user():
        response = client.post(
            f"/{name}s/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

        response = client.get(
            f"/{name}s/{identifier}?get_image=true",
            headers={"Authorization": "Fake token"},
        )
        org = response.json()
        del org["aiod_entry"]
        org["media"].append(
            {"name": "foo", "binary_blob": "bar="},
        )
        response = client.put(
            f"/{name}s/{identifier}",
            json=org,
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST, "No new binary may be added through a PUT request"

        org["media"].pop()
        response = client.put(
            f"/{name}s/{identifier}",
            json=org,
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()
