import datetime
import tempfile
from typing import Type
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from pydantic import Field
from sqlalchemy import String, create_engine
from sqlalchemy.orm import mapped_column, Mapped, Session
from starlette.testclient import TestClient

from converters import ResourceConverter
from database.model.resource import OrmResource
from routers import ResourceRouter
from schemas import AIoDResource


class OrmTestResource(OrmResource):
    __tablename__ = "test_resource"
    title: Mapped[str] = mapped_column(String(250), nullable=False)


class AIoDTestResource(AIoDResource):
    title: str = Field(max_length=250)


converter = Mock(spec=ResourceConverter)
converter.orm_to_aiod = Mock(
    return_value=AIoDTestResource(title="test", platform="example", platform_identifier=1)
)


class DeprecatedRouter(ResourceRouter[OrmTestResource, AIoDResource]):
    """A deprecated router, just used for testing."""

    @property
    def version(self) -> int:
        return 1

    @property
    def deprecated_from(self) -> datetime.date | None:
        return datetime.date(2022, 4, 21)

    @property
    def resource_name(self) -> str:
        return "test_resource"

    @property
    def resource_name_plural(self) -> str:
        return "test_resources"

    @property
    def aiod_class(self) -> Type[AIoDTestResource]:
        return AIoDTestResource

    @property
    def orm_class(self) -> Type[OrmTestResource]:
        return OrmTestResource

    @property
    def converter(self) -> ResourceConverter[AIoDTestResource, OrmTestResource]:
        return converter


@pytest.mark.parametrize(
    "verb,url",
    [
        ("get", "/test_resources/v1/"),
        ("get", "/platforms/example/test_resources/v1"),
        ("get", "/test_resources/v1/1"),
        ("get", "/platforms/example/test_resources/v1/1"),
        ("post", "/test_resources/v1/"),
        ("put", "/test_resources/v1/1"),
        ("delete", "/test_resources/v1/1"),
    ],
)
def test_deprecated_router(verb: str, url: str):
    temporary_file = tempfile.NamedTemporaryFile()
    engine = create_engine(f"sqlite:///{temporary_file.name}")
    OrmTestResource.metadata.create_all(engine)

    test_instance = OrmTestResource(title="A title", platform="example", platform_identifier="1")

    with Session(engine) as session:
        session.add(test_instance)
        session.commit()

    app = FastAPI()
    app.include_router(DeprecatedRouter().create(engine, ""))
    client = TestClient(app)

    kwargs = {}
    if verb == "post":
        converter.aiod_to_orm = Mock(
            return_value=OrmTestResource(title="test", platform="example", platform_identifier=1)
        )
        kwargs = {
            "json": AIoDTestResource(
                title="Another title", platform="example", platform_identifier="2"
            ).dict()
        }
    elif verb == "put" or verb == "delete":
        orm_resource = OrmTestResource(title="test", platform="example", platform_identifier=1)
        orm_resource.identifier = 1
        converter.aiod_to_orm = Mock(return_value=orm_resource)
        if verb == "put":
            kwargs = {
                "json": AIoDTestResource(
                    title="Title change", platform="example", platform_identifier="2"
                ).dict()
            }
    response = getattr(client, verb)(url, **kwargs)
    assert response.status_code == 200
    assert "deprecated" in response.headers
    assert response.headers.get("deprecated") == "Thu, 21 Apr 2022 00:00:00 GMT"
