from typing import Optional, List, Type
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from sqlmodel import Session, Field, Relationship, SQLModel
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model import AIAsset
from database.model.relationships import ResourceRelationshipSingle, ResourceRelationshipList
from database.model.named_relation import NamedRelation
from database.model.resource import Resource
from serialization import AttributeSerializer, FindByNameDeserializer, CastDeserializer
from routers import ResourceRouter


class EnumTest(NamedRelation, table=True):  # type: ignore [call-arg]
    """An "enum" that is located in an external table."""

    __tablename__ = "test_enum"

    objects: List["ObjectTest"] = Relationship(back_populates="named_string")


class ObjectEnum2ListLinkTest(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "test_enum_2_link"
    test_object_identifier: Optional[int] = Field(
        default=None, foreign_key="test_object.identifier", primary_key=True
    )
    test_enum_identifier: Optional[int] = Field(
        default=None, foreign_key="test_enum2.identifier", primary_key=True
    )


class EnumTest2(NamedRelation, table=True):  # type: ignore [call-arg]
    """An "enum" located in an external table, with a many-to-many relationship to ObjectTest."""

    __tablename__ = "test_enum2"
    objects: List["ObjectTest"] = Relationship(
        back_populates="named_string_list", link_model=ObjectEnum2ListLinkTest
    )


class ObjectRelatedObjectLinkTest(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "test_object_related_object_link"

    test_object_identifier: Optional[int] = Field(
        default=None, foreign_key="test_object.identifier", primary_key=True
    )
    test_enum_identifier: Optional[int] = Field(
        default=None, foreign_key="test_related_object.identifier", primary_key=True
    )


class RelatedObjectTest(SQLModel):
    field1: str = Field(max_length=150)
    field2: str = Field(max_length=150)


class RelatedObjectTestOrm(RelatedObjectTest, table=True):  # type: ignore [call-arg]
    """A related object that should be shown completely"""

    __tablename__ = "test_related_object"

    identifier: int | None = Field(primary_key=True)
    test_objects: List["ObjectTest"] = Relationship(
        back_populates="related_objects", link_model=ObjectRelatedObjectLinkTest
    )


class ObjectBaseTest(Resource):
    title: str = Field(max_length=100, description="title description")


class ObjectTest(ObjectBaseTest, table=True):  # type: ignore [call-arg]
    __tablename__ = "test_object"

    identifier: str = Field(primary_key=True, foreign_key="ai_asset.identifier")
    named_string_identifier: Optional[int] = Field(default=None, foreign_key="test_enum.identifier")
    named_string: Optional[EnumTest] = Relationship(back_populates="objects")
    named_string_list: List[EnumTest2] = Relationship(
        back_populates="objects", link_model=ObjectEnum2ListLinkTest
    )
    related_objects: List[RelatedObjectTestOrm] = Relationship(
        back_populates="test_objects", link_model=ObjectRelatedObjectLinkTest
    )

    class RelationshipConfig:
        named_string: Optional[str] = ResourceRelationshipSingle(
            description="this is a test for a string stored in a separate table",
            identifier_name="named_string_identifier",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(EnumTest),
            example="test",
        )
        named_string_list: List[str] = ResourceRelationshipList(
            description="this is a test for a list of strings",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(EnumTest2),
            example=["test1", "test2"],
        )
        related_objects: List[RelatedObjectTest] = ResourceRelationshipList(
            description="this is a test for a list of objects",
            deserializer=CastDeserializer(RelatedObjectTestOrm),
        )


class RouterObjectTest(ResourceRouter):
    @property
    def version(self) -> int:
        return 0

    @property
    def resource_name(self) -> str:
        return "test_resource"

    @property
    def resource_name_plural(self) -> str:
        return "test_resources"

    @property
    def resource_class(self) -> Type[ObjectTest]:
        return ObjectTest


@pytest.fixture
def client_with_ObjectTest(engine_test_resource) -> TestClient:
    with Session(engine_test_resource) as session:
        named1, named2 = EnumTest(name="named_string1"), EnumTest(name="named_string2")
        enum1, enum2, enum3 = EnumTest2(name="1"), EnumTest2(name="2"), EnumTest2(name="3")
        session.add_all(
            [
                AIAsset(type="test_object"),
                AIAsset(type="test_object"),
                AIAsset(type="test_object"),
                AIAsset(type="test_object"),
                named1,
                named2,
                enum1,
                enum2,
                enum3,
                ObjectTest(
                    identifier=1,
                    title="object 1",
                    named_string=named1,
                    named_string_list=[enum1, enum2],
                ),
                ObjectTest(identifier=2, title="object 2", named_string=named1),
                ObjectTest(
                    identifier=3,
                    title="object 3",
                    named_string=named2,
                    named_string_list=[enum2, enum3],
                ),
                ObjectTest(identifier=4, title="object 4"),
            ]
        )
        session.commit()
    app = FastAPI()
    app.include_router(RouterObjectTest().create(engine_test_resource, ""))
    return TestClient(app)


def test_get_happy_path(client_with_ObjectTest: TestClient):
    response = client_with_ObjectTest.get("/test_resources/v0/1")
    assert response.status_code == 200
    response_json = response.json()

    assert response_json["identifier"] == 1
    assert response_json["title"] == "object 1"
    assert response_json["named_string"] == "named_string1"
    assert response_json["named_string_list"] == ["1", "2"]
    assert "deprecated" not in response.headers


def test_get_all_happy_path(client_with_ObjectTest: TestClient):
    response = client_with_ObjectTest.get("/test_resources/v0")
    assert response.status_code == 200
    response_json = response.json()
    assert "deprecated" not in response.headers

    assert len(response_json) == 4
    r1, r2, r3, r4 = sorted(response_json, key=lambda v: v["title"])
    assert r1["named_string"] == "named_string1"
    assert r1["named_string_list"] == ["1", "2"]
    assert r2["named_string"] == "named_string1"
    assert r2["named_string_list"] == []
    assert r3["named_string"] == "named_string2"
    assert r3["named_string_list"] == ["2", "3"]
    assert "named_string" not in r4


def test_post_happy_path(client_with_ObjectTest: TestClient, mocked_privileged_token: Mock):
    keycloak_openid.decode_token = mocked_privileged_token
    response = client_with_ObjectTest.post(
        "/test_resources/v0",
        json={
            "title": "title",
            "named_string": "named_string1",
            "named_string_list": ["1", "4"],
            "related_objects": [
                {"field1": "val1.1", "field2": "val1.2"},
                {"field1": "val2.1", "field2": "val2.2"},
            ],
        },
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200
    objects = client_with_ObjectTest.get("/test_resources/v0").json()
    obj = objects[-1]
    assert obj["identifier"] == 5
    assert obj["title"] == "title"
    assert obj["named_string"] == "named_string1"
    assert sorted(obj["named_string_list"]) == ["1", "4"]
    related_objects = sorted(obj["related_objects"], key=lambda v: v["field1"])
    assert "identifier" not in related_objects[0]
    assert related_objects[0]["field1"] == "val1.1"
    assert related_objects[0]["field2"] == "val1.2"
    assert "identifier" not in related_objects[1]
    assert related_objects[1]["field1"] == "val2.1"
    assert related_objects[1]["field2"] == "val2.2"


def test_put_happy_path(client_with_ObjectTest: TestClient, mocked_privileged_token: Mock):
    keycloak_openid.decode_token = mocked_privileged_token
    response = client_with_ObjectTest.put(
        "/test_resources/v0/4",
        json={
            "title": "new title",
            "named_string": "new_string",
            "named_string_list": ["1", "4", "9"],
            "related_objects": [
                {"field1": "val1-1", "field2": "val1-2"},
                {"field1": "val2-1", "field2": "val2-2"},
            ],
        },
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200
    changed_resource = client_with_ObjectTest.get("/test_resources/v0/4").json()
    assert changed_resource["title"] == "new title"
    assert changed_resource["named_string"] == "new_string"
    assert sorted(changed_resource["named_string_list"]) == ["1", "4", "9"]
    related_objects = sorted(changed_resource["related_objects"], key=lambda v: v["field1"])
    assert "identifier" not in related_objects[0]
    assert related_objects[0]["field1"] == "val1-1"
    assert related_objects[0]["field2"] == "val1-2"
    assert "identifier" not in related_objects[1]
    assert related_objects[1]["field1"] == "val2-1"
    assert related_objects[1]["field2"] == "val2-2"

    # TODO: test that the same instance of RelatedObjectORM is updated if new values are added
