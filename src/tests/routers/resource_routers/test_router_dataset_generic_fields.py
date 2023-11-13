import copy
import time
from datetime import datetime
from unittest.mock import Mock

import dateutil.parser
import pytz
import typing
from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model import field_length
from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.dataset.dataset import Dataset
from database.model.helper_functions import all_annotations
from database.model.knowledge_asset.publication import Publication


def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset: dict,
    person: Person,
    publication: Publication,
    contact: Contact,
):
    keycloak_openid.userinfo = mocked_privileged_token
    with Session(engine) as session:
        session.add(person)
        session.merge(publication)
        session.add(contact)
        session.commit()

    body = copy.deepcopy(body_asset)
    body["aiod_entry"]["editor"] = [1]
    body["aiod_entry"]["status"] = "published"
    body["contact"] = [1]
    body["creator"] = [1]
    body["citation"] = [1]
    description_plain = "a" * field_length.MAX_TEXT
    description_html = f"<p>{'a' * (field_length.MAX_TEXT - 7)}</p>"
    body["description"] = {"plain": description_plain, "html": description_html}

    datetime_create_request = datetime.utcnow().replace(tzinfo=pytz.utc)
    response = client.post("/datasets/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/datasets/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["ai_resource_identifier"] == 3
    assert response_json["ai_asset_identifier"] == 2

    assert response_json["platform"] == "example"
    assert response_json["platform_resource_identifier"] == "1"
    assert response_json["aiod_entry"]["editor"] == [1]
    assert response_json["aiod_entry"]["status"] == "published"
    date_created = dateutil.parser.parse(response_json["aiod_entry"]["date_created"] + "Z")
    date_modified = dateutil.parser.parse(response_json["aiod_entry"]["date_modified"] + "Z")
    assert 0 < (date_created - datetime_create_request).total_seconds() < 0.2
    assert 0 < (date_modified - datetime_create_request).total_seconds() < 0.2

    assert response_json["name"] == "The name"
    assert response_json["description"]["plain"] == description_plain
    assert response_json["description"]["html"] == description_html
    assert set(response_json["alternate_name"]) == {"alias1", "alias2"}
    assert set(response_json["keyword"]) == {"tag1", "tag2"}
    assert set(response_json["relevant_link"]) == {
        "https://www.example.com/a_relevant_link",
        "https://www.example.com/another_relevant_link",
    }
    assert response_json["is_accessible_for_free"]

    assert response_json["application_area"] == ["Voice Assistance"]
    assert response_json["industrial_sector"] == ["eCommerce"]
    assert response_json["research_area"] == ["Explainable AI"]
    assert response_json["scientific_domain"] == ["Voice Recognition"]
    assert response_json["contact"] == [1]
    assert response_json["creator"] == [1]
    assert response_json["citation"] == [1]

    (media,) = response_json["media"]
    assert media["name"] == "Resource logo"
    assert media["content_url"] == "https://www.example.com/resource.png"

    (distribution,) = response_json["distribution"]
    assert distribution["name"] == "resource.pdf"
    assert distribution["content_url"] == "https://www.example.com/resource.pdf"

    assert response_json["date_published"] == "2022-01-01T15:15:00"
    assert response_json["license"] == "https://creativecommons.org/licenses/by/4.0/"
    assert response_json["version"] == "1.a"
    notes = [note["value"] for note in response_json["note"]]
    assert len(notes) == 2
    assert "A note" in notes
    lorem = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
        "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
        "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute "
        "irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
        "deserunt mollit anim id est laborum."
    )
    assert lorem in notes

    body["platform_resource_identifier"] = "2"
    body["name"] = "new name"
    body["version"] = "1.b"
    body["distribution"] = [
        {
            "name": "downloadable instance of this resource",
            "content_url": "https://www.example.com/resource_new.pdf",
        }
    ]

    time.sleep(0.15)
    datetime_update_request = datetime.utcnow().replace(tzinfo=pytz.utc)
    response = client.put("/datasets/v1/1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/datasets/v1/1")
    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["ai_resource_identifier"] == 3
    assert response_json["ai_asset_identifier"] == 2

    date_created = dateutil.parser.parse(response_json["aiod_entry"]["date_created"] + "Z")
    date_modified = dateutil.parser.parse(response_json["aiod_entry"]["date_modified"] + "Z")
    assert 0 < (date_created - datetime_create_request).total_seconds() < 0.1
    assert 0 < (date_modified - datetime_update_request).total_seconds() < 0.1

    assert response_json["platform"] == "example"
    assert response_json["platform_resource_identifier"] == "2"

    assert response_json["name"] == "new name"

    (distribution,) = response_json["distribution"]
    assert distribution["name"] == "downloadable instance of this resource"
    assert distribution["content_url"] == "https://www.example.com/resource_new.pdf"

    assert response_json["version"] == "1.b"


def test_post_duplicate_named_relations(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
):
    """
    Unittest mirroring situation reported during the data migration of AI4EU news.
    """
    keycloak_openid.userinfo = mocked_privileged_token

    def create_body(i: int, *keywords):
        return {"name": f"dataset{i}", "keyword": keywords}

    body1 = create_body(1, "AI")
    body2 = create_body(
        2,
        "AI",
        "ArtificialIntelligence",
        "digitaltransformation",
        "smartcities",
        "mobility",
        "greendeal",
        "energy",
    )
    body3 = create_body(3)
    body4 = create_body(
        3,
        "AI4EU Experiments",
        "solutions",
        "pipelines",
        "hybrid AI",
        "modular AI",
        "reliability",
        "explainability",
        "trustworthiness",
        "ArtificialIntelligence",
    )

    client.post("/news/v1", json=body1, headers={"Authorization": "Fake token"})
    response = client.post("/news/v1", json=body2, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    response = client.get("/news/v1/2")
    assert set(response.json()["keyword"]) == {
        "AI",
        "ArtificialIntelligence",
        "digitaltransformation",
        "smartcities",
        "mobility",
        "greendeal",
        "energy",
    }

    client.post("/news/v1", json=body3, headers={"Authorization": "Fake token"})
    response = client.get("/news/v1/3")
    assert len(response.json()["keyword"]) == 0
    client.post("/news/v1", json=body4, headers={"Authorization": "Fake token"})
    response = client.get("/news/v1/4")
    assert set(response.json()["keyword"]) == {
        "AI4EU Experiments",
        "solutions",
        "pipelines",
        "hybrid AI",
        "modular AI",
        "reliability",
        "explainability",
        "trustworthiness",
        "ArtificialIntelligence",
    }


def test_post_editors(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
):
    """
    Unittest mirroring situation reported during the data migration of AI4EU events.
    """
    keycloak_openid.userinfo = mocked_privileged_token
    headers = {"Authorization": "Fake token"}
    client.post("/persons/v1", json={"name": "1"}, headers=headers)
    client.post("/persons/v1", json={"name": "2"}, headers=headers)
    client.post("/persons/v1", json={"name": "3"}, headers=headers)

    def assert_editors_are_stored(id_: str, *editors: int):
        body = {
            "platform": "example",
            "platform_resource_identifier": id_,
            "name": "How user evaluation changed in times of COVID-19",
            "aiod_entry": {"editor": editors, "status": "published"},
        }
        response = client.post("/events/v1", json=body, headers=headers)
        assert response.status_code == 200, response.json()
        response = client.get(f"/events/v1/{response.json()['identifier']}")
        assert response.status_code == 200, response.json()
        editors_actual = response.json()["aiod_entry"]["editor"]
        assert set(editors_actual) == set(editors)

    assert_editors_are_stored("34", 1, 2, 3)
    assert_editors_are_stored("37", 1, 2)
    assert_editors_are_stored("36", 1, 2)


def test_create_aiod_entry(client: TestClient, engine: Engine, mocked_privileged_token: Mock):
    keycloak_openid.userinfo = mocked_privileged_token
    body = {"name": "news"}
    start = datetime.now(pytz.utc)
    response = client.post("/news/v1", json=body, headers={"Authorization": "Fake token"})
    end = datetime.now(pytz.utc)
    assert response.status_code == 200, response.json()
    response = client.get("/news/v1/1")
    resource_json = response.json()

    assert "aiod_entry" in resource_json
    date_created = dateutil.parser.parse(resource_json["aiod_entry"]["date_created"] + "Z")
    date_modified = dateutil.parser.parse(resource_json["aiod_entry"]["date_modified"] + "Z")
    assert start < date_created < end
    assert start < date_modified < end

    assert resource_json["ai_resource_identifier"] == 1


def test_update_aiod_entry(client: TestClient, engine: Engine, mocked_privileged_token: Mock):
    keycloak_openid.userinfo = mocked_privileged_token
    body = {"name": "news"}
    start = datetime.now(pytz.utc)
    response = client.post("/news/v1", json=body, headers={"Authorization": "Fake token"})
    end = datetime.now(pytz.utc)
    assert response.status_code == 200, response.json()

    put_body = {"name": "news", "aiod_entry": {"status": "published"}}
    response = client.put("/news/v1/1", json=put_body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/news/v1/1")
    resource_json = response.json()

    assert "aiod_entry" in resource_json
    date_created = dateutil.parser.parse(resource_json["aiod_entry"]["date_created"] + "Z")
    date_modified = dateutil.parser.parse(resource_json["aiod_entry"]["date_modified"] + "Z")
    assert start < date_created < end
    assert end < date_modified

    assert resource_json["aiod_entry"]["status"] == "published"
    with Session(engine) as session:
        entries = session.scalars(select(AIoDEntryORM)).all()
        assert len(entries) == 1


def assert_distributions(client: TestClient, engine: Engine, *content_urls: str):
    response = client.get("/datasets/v1/1")
    distributions = response.json()["distribution"]
    assert {distribution["content_url"] for distribution in distributions} == set(content_urls)

    (distribution_class,) = typing.get_args(all_annotations(Dataset)["distribution"])
    with Session(engine) as session:
        distributions = session.scalars(select(distribution_class)).all()
        assert {distribution.content_url for distribution in distributions} == set(content_urls)


def test_update_distribution(client: TestClient, engine: Engine, mocked_privileged_token: Mock):
    keycloak_openid.userinfo = mocked_privileged_token
    body = {"name": "dataset", "distribution": [{"content_url": "url"}]}
    response = client.post("/datasets/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_distributions(client, engine, "url")

    body = {"name": "dataset", "distribution": [{"content_url": "url2"}, {"content_url": "test"}]}
    response = client.put("/datasets/v1/1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_distributions(client, engine, "url2", "test")

    body = {"name": "dataset", "distribution": [{"content_url": "url"}]}
    response = client.put("/datasets/v1/1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_distributions(client, engine, "url")


def assert_relations(
    client: TestClient,
    type_: str,
    has_part: list[int] | None = None,
    is_part_of: list[int] | None = None,
    relevant_resource: list[int] | None = None,
    relevant_to: list[int] | None = None,
):
    response = client.get(f"/{type_}/v1/1")
    resource = response.json()
    assert response.status_code == 200, resource
    assert resource["has_part"] == (has_part or [])
    assert resource["is_part_of"] == (is_part_of or [])
    assert resource["relevant_resource"] == (relevant_resource or [])
    assert resource["relevant_to"] == (relevant_to or [])


def test_relations_between_resources(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset: dict,
    dataset: Dataset,
    publication: Publication,
    organisation: Organisation,
):
    keycloak_openid.userinfo = mocked_privileged_token

    with Session(engine) as session:
        session.add(dataset)
        session.merge(publication)
        session.merge(organisation)
        session.commit()

    body = {"name": "news", "has_part": [1], "is_part_of": [2], "relevant_resource": [3]}
    response = client.post("/news/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_relations(client, "datasets", is_part_of=[4])
    assert_relations(client, "publications", has_part=[4])
    assert_relations(client, "organisations", relevant_to=[4])

    body = {
        "name": "news",
        "has_part": [2],
        "is_part_of": [1, 3],
        "relevant_resource": [],
    }
    response = client.put("/news/v1/1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_relations(client, "datasets", has_part=[4])
    assert_relations(client, "publications", is_part_of=[4])
    assert_relations(client, "organisations", has_part=[4])

    body = {
        "name": "news",
        "has_part": [],
        "is_part_of": [],
        "relevant_resource": [1, 2],
        "relevant_to": [3],
    }
    response = client.put("/news/v1/1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_relations(client, "datasets", relevant_to=[4])
    assert_relations(client, "publications", relevant_to=[4])
    assert_relations(client, "organisations", relevant_resource=[4])

    body = {"name": "news", "has_part": [1], "is_part_of": [2], "relevant_resource": [3]}
    response = client.put("/news/v1/1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    response = client.delete("/news/v1/1", headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
