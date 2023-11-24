from typing import Any, Type

import pytest
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy.engine import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from converters.schema_converters.schema_converter import SchemaConverter
from tests.testutils.test_resource import RouterTestResource, TestResource


class SchemaClass(BaseModel):
    """Alternative schema for the AIoDTestResource, only used for unittests"""

    title_with_alternative_name: str = Field(max_length=250)


class SchemaConverterTestResource(SchemaConverter[TestResource, SchemaClass]):
    """Converting the AIoDTestResource into SchemaClass, only used for unittests"""

    @property
    def to_class(self) -> Type[SchemaClass]:
        return SchemaClass

    def convert(self, session: Session, aiod: TestResource) -> SchemaClass:
        return SchemaClass(title_with_alternative_name=aiod.title)


class RouterWithOtherSchema(RouterTestResource):
    """Router with "aiod" and "other-schema" as possible output format, used only for unittests"""

    @property
    def schema_converters(self) -> dict[str, SchemaConverter[TestResource, Any]]:
        return {"other-schema": SchemaConverterTestResource()}


@pytest.fixture(scope="module")
def client_test_resource_other_schema() -> TestClient:
    """A Startlette TestClient including routes to the TestResource, using schemas "aiod" and
    "other-schema" """
    app = FastAPI()
    app.include_router(RouterWithOtherSchema().create(""))
    return TestClient(app)


@pytest.mark.parametrize("schema_string", ["", "?schema=aiod"])
def test_resources_aiod(
    client_test_resource: TestClient,
    client_test_resource_other_schema: TestClient,
    engine_test_resource_filled: Engine,
    schema_string: str,
):

    for client in [client_test_resource_other_schema, client_test_resource]:
        response = client.get("/test_resources/v0" + schema_string)
        assert response.status_code == 200, response.json()
        json_ = response.json()
        assert len(json_) == 1
        assert json_[0]["title"] == "A title"
        assert "title_with_alternative_name" not in json_[0]


@pytest.mark.parametrize("schema_string", ["", "?schema=aiod"])
def test_resource_aiod(
    client_test_resource: TestClient,
    client_test_resource_other_schema: TestClient,
    engine_test_resource_filled: Engine,
    schema_string: str,
):
    for client in [client_test_resource_other_schema, client_test_resource]:
        response = client.get("/test_resources/v0/1" + schema_string)
        assert response.status_code == 200, response.json()
        json_ = response.json()
        assert json_["title"] == "A title"
        assert "title_with_alternative_name" not in json_


@pytest.mark.parametrize("url_part", ["?schema=other-schema", "/1?schema=other-schema"])
def test_aiod_only_other_schema(client_test_resource: TestClient, url_part: str):
    response = client_test_resource.get("/test_resources/v0" + url_part)
    assert response.status_code == 422, response.json()
    assert response.json()["detail"][0]["msg"] == "unexpected value; permitted: 'aiod'"


def test_resources_other_schema(
    client_test_resource_other_schema: TestClient, engine_test_resource_filled: Engine
):
    response = client_test_resource_other_schema.get("/test_resources/v0?schema=other-schema")
    assert response.status_code == 200, response.json()
    json_ = response.json()
    assert len(json_) == 1
    assert json_[0]["title_with_alternative_name"] == "A title"
    assert "title" not in json_[0]


def test_resource_other_schema(
    client_test_resource_other_schema: TestClient, engine_test_resource_filled: Engine
):
    response = client_test_resource_other_schema.get("/test_resources/v0/1?schema=other-schema")
    assert response.status_code == 200, response.json()
    json_ = response.json()
    assert json_["title_with_alternative_name"] == "A title"
    assert "title" not in json_


@pytest.mark.parametrize(
    "url", ["/test_resources/v0?schema=nonexistent", "/test_resources/v0/1?schema=nonexistent"]
)
def test_nonexistent_schema(client_test_resource_other_schema: TestClient, url: str):
    response = client_test_resource_other_schema.get(url)
    assert response.status_code == 422, response.json()
    msg = response.json()["detail"][0]["msg"]
    assert msg == "unexpected value; permitted: 'aiod', 'other-schema'"
