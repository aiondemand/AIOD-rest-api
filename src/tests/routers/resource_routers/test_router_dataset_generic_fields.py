import copy
import time
from datetime import datetime
from functools import partial
from http import HTTPStatus
from unittest.mock import Mock

import dateutil.parser
import pytest
import pytz
from sqlalchemy import delete
from sqlmodel import select
from starlette.testclient import TestClient

from database.model import field_length
from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.annotations import datatype_of_field
from database.model.concept.aiod_entry import AIoDEntryORM, EntryStatus
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.model.news.news import News
from database.session import DbSession
from tests.testutils.users import logged_in_user


def test_happy_path(
    client: TestClient,
    body_asset: dict,
    person: Person,
    publication: Publication,
    contact: Contact,
    auto_publish: None,
):
    person_identifier = person.identifier
    contact_identifier = contact.identifier
    publication_identifier = publication.identifier

    with DbSession() as session:
        session.add(person)
        session.add(contact)
        session.merge(publication)
        session.commit()

    body = copy.deepcopy(body_asset)
    body["aiod_entry"]["editor"] = [person_identifier]
    body["contact"] = [contact_identifier]
    body["creator"] = [contact_identifier]
    body["citation"] = [publication_identifier]
    description_plain = "a" * field_length.MAX_TEXT
    description_html = f"<p>{'a' * (field_length.MAX_TEXT - 7)}</p>"
    body["description"] = {"plain": description_plain, "html": description_html}

    datetime_create_request = datetime.utcnow().replace(tzinfo=pytz.utc)
    with logged_in_user():
        response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/datasets/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == identifier
    assert response_json["ai_resource_identifier"] == identifier
    assert response_json["ai_asset_identifier"] == identifier

    assert response_json["platform"] == "example"
    assert response_json["platform_resource_identifier"] == "1"
    assert response_json["aiod_entry"]["editor"] == [person_identifier]
    assert response_json["aiod_entry"]["status"] == EntryStatus.PUBLISHED
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

    assert response_json["application_area"] == ["voice assistance"]
    assert response_json["industrial_sector"] == ["ecommerce"]
    assert response_json["research_area"] == ["explainable ai"]
    assert response_json["scientific_domain"] == ["voice recognition"]
    assert response_json["contact"] == [contact_identifier]
    assert response_json["creator"] == [contact_identifier]
    assert response_json["citation"] == [publication_identifier]

    (media,) = response_json["media"]
    assert media["name"] == "Resource logo"
    assert media["content_url"] == "https://www.example.com/resource.png"

    (distribution,) = response_json["distribution"]
    assert distribution["name"] == "resource.pdf"
    assert distribution["content_url"] == "https://www.example.com/resource.pdf"

    assert response_json["date_published"] == "2022-01-01T15:15:00"
    assert response_json["license"] == "CC-BY-4.0"
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
    with logged_in_user():
        response = client.put(f"/datasets/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get(f"/datasets/{identifier}")
    response_json = response.json()
    assert response_json["identifier"] == identifier
    assert response_json["ai_resource_identifier"] == identifier
    assert response_json["ai_asset_identifier"] == identifier

    date_created = dateutil.parser.parse(response_json["aiod_entry"]["date_created"] + "Z")
    date_modified = dateutil.parser.parse(response_json["aiod_entry"]["date_modified"] + "Z")
    assert 0 < (date_created - datetime_create_request).total_seconds() < 0.2
    assert 0 < (date_modified - datetime_update_request).total_seconds() < 0.4

    assert response_json["platform"] == "example"
    assert response_json["platform_resource_identifier"] == "2"

    assert response_json["name"] == "new name"

    (distribution,) = response_json["distribution"]
    assert distribution["name"] == "downloadable instance of this resource"
    assert distribution["content_url"] == "https://www.example.com/resource_new.pdf"

    assert response_json["version"] == "1.b"


def test_post_duplicate_named_relations(
    client: TestClient,
    auto_publish: None,
):
    """
    Unittest mirroring situation reported during the data migration of AI4EU news.
    """

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

    post_news = partial(client.post, "/news", headers={"Authorization": "Fake token"})
    identifiers = []
    with (logged_in_user()):
        for body in [body1, body2, body3, body4]:
            response = post_news(json=body)
            assert response.status_code == HTTPStatus.OK
            identifiers.append(response.json()['identifier'])

    response = client.get(f"/news/{identifiers[1]}")
    assert response.status_code == HTTPStatus.OK, response.json()
    assert set(response.json()["keyword"]) == {
        "ai",
        "artificialintelligence",
        "digitaltransformation",
        "smartcities",
        "mobility",
        "greendeal",
        "energy",
    }

    response = client.get(f"/news/{identifiers[2]}")
    assert len(response.json()["keyword"]) == 0
    response = client.get(f"/news/{identifiers[3]}")
    assert set(response.json()["keyword"]) == {
        "ai4eu experiments",
        "solutions",
        "pipelines",
        "hybrid ai",
        "modular ai",
        "reliability",
        "explainability",
        "trustworthiness",
        "artificialintelligence",
    }


def test_post_duplicate_named_relations_with_different_capitals(
    client: TestClient,
    mocked_privileged_token: Mock,
):
    def create_body(i: int, *keywords):
        return {"name": f"dataset{i}", "keyword": keywords}

    body1 = create_body(1, "AI")
    body2 = create_body(2, "ai")
    client.post("/news", json=body1, headers={"Authorization": "Fake token"})
    response = client.post("/news", json=body2, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()


def test_post_editors(
    client: TestClient,
    auto_publish: None,
):
    """
    Unittest mirroring situation reported during the data migration of AI4EU events.
    """
    headers = {"Authorization": "Fake token"}
    identifiers = []
    with logged_in_user():
        for i in range(1, 4):
            response = client.post("/persons", json={"name": str(i)}, headers=headers)
            identifiers.append(response.json()['identifier'])

    def assert_editors_are_stored(id_: str, *editors: int):
        body = {
            "platform": "example",
            "platform_resource_identifier": id_,
            "name": "How user evaluation changed in times of COVID-19",
            "aiod_entry": {"editor": editors},
        }
        with logged_in_user():
            response = client.post("/events", json=body, headers=headers)
        assert response.status_code == 200, response.json()
        response = client.get(f"/events/{response.json()['identifier']}")
        assert response.status_code == 200, response.json()
        editors_actual = response.json()["aiod_entry"]["editor"]
        assert set(editors_actual) == set(editors)

    assert_editors_are_stored("34", *identifiers)
    assert_editors_are_stored("37", *identifiers[:2])
    assert_editors_are_stored("36", *identifiers[:2])


def test_create_aiod_entry(client: TestClient, auto_publish):
    body = {"name": "news"}
    start = datetime.now(pytz.utc)
    with logged_in_user():
        response = client.post("/news", json=body, headers={"Authorization": "Fake token"})
    end = datetime.now(pytz.utc)
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']
    response = client.get(f"/news/{identifier}")
    resource_json = response.json()

    assert "aiod_entry" in resource_json
    date_created = dateutil.parser.parse(resource_json["aiod_entry"]["date_created"] + "Z")
    date_modified = dateutil.parser.parse(resource_json["aiod_entry"]["date_modified"] + "Z")
    assert start < date_created < end
    assert start < date_modified < end

    assert resource_json["ai_resource_identifier"] == identifier


def test_update_aiod_entry(
    client: TestClient,
    mocked_privileged_token: Mock,
    person: Person,
    auto_publish: None,
):
    with DbSession() as session:
        session.add(person)
        session.commit()
        session.refresh(person)

    body = {"name": "news"}
    start = datetime.now(pytz.utc)
    response = client.post("/news", json=body, headers={"Authorization": "Fake token"})
    end = datetime.now(pytz.utc)
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    put_body = {"name": "news", "aiod_entry": {"editor": [person.identifier]}}
    response = client.put(f"/news/{identifier}", json=put_body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get(f"/news/{identifier}")
    resource_json = response.json()

    assert "aiod_entry" in resource_json
    date_created = dateutil.parser.parse(resource_json["aiod_entry"]["date_created"] + "Z")
    date_modified = dateutil.parser.parse(resource_json["aiod_entry"]["date_modified"] + "Z")
    assert start < date_created < end
    assert end < date_modified

    assert resource_json["aiod_entry"]["editor"] == [person.identifier]
    with DbSession() as session:
        entries = session.scalars(select(AIoDEntryORM)).all()
        assert len(entries) == 2


def assert_distributions(client: TestClient, identifier: str, *content_urls: str):
    response = client.get(f"/datasets/{identifier}")
    distributions = response.json()["distribution"]
    assert {distribution["content_url"] for distribution in distributions} == set(content_urls)

    distribution_class = datatype_of_field(Dataset, "distribution")
    with DbSession() as session:
        distributions = session.scalars(select(distribution_class)).all()
        assert {distribution.content_url for distribution in distributions} == set(content_urls)


def test_update_distribution(client: TestClient, mocked_privileged_token: Mock, auto_publish: None):
    body = {"name": "dataset", "distribution": [{"content_url": "url"}]}
    response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']
    assert_distributions(client, identifier, "url")

    body = {"name": "dataset", "distribution": [{"content_url": "url2"}, {"content_url": "test"}]}
    response = client.put(f"/datasets/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_distributions(client, identifier, "url2", "test")

    body = {"name": "dataset", "distribution": [{"content_url": "url"}]}
    response = client.put(f"/datasets/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_distributions(client, identifier, "url")


def assert_relations(
    client: TestClient,
    identifier: str,
    type_: str,
    has_part: list[int] | None = None,
    is_part_of: list[int] | None = None,
    relevant_resource: list[int] | None = None,
    relevant_to: list[int] | None = None,
):
    response = client.get(f"/{type_}/{identifier}")
    resource = response.json()
    assert response.status_code == 200, resource
    assert resource["has_part"] == (has_part or [])
    assert resource["is_part_of"] == (is_part_of or [])
    assert resource["relevant_resource"] == (relevant_resource or [])
    assert resource["relevant_to"] == (relevant_to or [])


def test_relations_between_resources(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_asset: dict,
    dataset: Dataset,
    publication: Publication,
    organisation: Organisation,
    auto_publish: None,
):
    with DbSession() as session:
        session.add(dataset)
        session.merge(publication)
        session.merge(organisation)
        session.commit()
        session.refresh(dataset)

    body = {"name": "news", "has_part": [dataset.identifier], "is_part_of": [publication.identifier], "relevant_resource": [organisation.identifier]}
    response = client.post("/news", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()["identifier"]
    assert_relations(client, dataset.identifier, "datasets", is_part_of=[identifier])
    assert_relations(client, publication.identifier, "publications", has_part=[identifier])
    assert_relations(client, organisation.identifier,"organisations", relevant_to=[identifier])

    body = {
        "name": "news",
        "has_part": [publication.identifier],
        "is_part_of": [dataset.identifier, organisation.identifier],
        "relevant_resource": [],
    }
    response = client.put(f"/news/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_relations(client, dataset.identifier, "datasets", has_part=[identifier])
    assert_relations(client, publication.identifier, "publications", is_part_of=[identifier])
    assert_relations(client, organisation.identifier, "organisations", has_part=[identifier])

    body = {
        "name": "news",
        "has_part": [],
        "is_part_of": [],
        "relevant_resource": [dataset.identifier, publication.identifier],
        "relevant_to": [organisation.identifier],
    }
    response = client.put(f"/news/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert_relations(client, dataset.identifier, "datasets", relevant_to=[identifier])
    assert_relations(client, publication.identifier, "publications", relevant_to=[identifier])
    assert_relations(client, organisation.identifier, "organisations", relevant_resource=[identifier])

    body = {"name": "news", "has_part": [], "is_part_of": [], "relevant_resource": []}
    response = client.put(f"/news/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    with DbSession() as session:
        session.exec(delete(News))  # hard delete
        session.commit()
    assert response.status_code == 200, response.json()
    assert_relations(client,dataset.identifier, "datasets")
    assert_relations(client,publication.identifier, "publications")
    assert_relations(client, organisation.identifier, "organisations")
