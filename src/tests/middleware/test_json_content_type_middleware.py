from fastapi import FastAPI, File, UploadFile
from fastapi.testclient import TestClient

from middleware.json_content_type import JsonContentTypeMiddleware

import sys
import os
sys.path.append(os.path.abspath("src"))

def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(JsonContentTypeMiddleware)

    @app.post("/json")
    async def post_json(payload: dict):
        return payload

    @app.put("/json")
    async def put_json(payload: dict):
        return payload

    @app.patch("/json")
    async def patch_json(payload: dict):
        return payload

    @app.post("/query-only")
    async def query_only(value: str):
        return {"value": value}

    @app.post("/organisations/{identifier}/image")
    async def upload_image(identifier: str, file: UploadFile = File(...)):
        return {"identifier": identifier, "filename": file.filename}

    return app


def test_post_with_json_content_type_passes():
    client = TestClient(_build_app())
    response = client.post("/json", json={"x": 1})
    assert response.status_code == 200
    assert response.json() == {"x": 1}


def test_put_with_invalid_content_type_returns_415():
    client = TestClient(_build_app())
    response = client.put(
        "/json",
        data='{"x": 1}',
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 415
    assert "application/json" in response.json()["detail"]


def test_patch_without_content_type_returns_415_when_body_present():
    client = TestClient(_build_app())
    response = client.patch("/json", content=b'{"x": 1}')
    assert response.status_code == 415
    assert "application/json" in response.json()["detail"]


def test_post_without_body_does_not_require_json_content_type():
    client = TestClient(_build_app())
    response = client.post("/query-only", params={"value": "ok"})
    assert response.status_code == 200
    assert response.json() == {"value": "ok"}


def test_docs_endpoints_are_not_blocked():
    client = TestClient(_build_app())
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_multipart_upload_endpoint_is_not_blocked():
    client = TestClient(_build_app())
    files = {"file": ("logo.png", b"image-bytes", "image/png")}
    response = client.post("/organisations/org_foo/image", files=files)
    assert response.status_code == 200
    assert response.json()["filename"] == "logo.png"


def test_json_with_charset_header_passes():
    client = TestClient(_build_app())
    response = client.post(
        "/json",
        data='{"x": 1}',
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    assert response.status_code == 200


def test_content_type_case_insensitive():
    client = TestClient(_build_app())
    response = client.post(
        "/json",
        data='{"x": 1}',
        headers={"Content-Type": "Application/JSON"},
    )
    assert response.status_code == 200


def test_invalid_json_like_content_type_rejected():
    client = TestClient(_build_app())
    response = client.post(
        "/json",
        data='{"x": 1}',
        headers={"Content-Type": "text/application-json"},
    )
    assert response.status_code == 415



if __name__ == "__main__":
    test_post_with_json_content_type_passes()
    test_put_with_invalid_content_type_returns_415()
    test_patch_without_content_type_returns_415_when_body_present()
    test_post_without_body_does_not_require_json_content_type()
    test_docs_endpoints_are_not_blocked()
    test_multipart_upload_endpoint_is_not_blocked()
    test_json_with_charset_header_passes()
    test_content_type_case_insensitive()
    test_invalid_json_like_content_type_rejected()
    print("All tests passed!")