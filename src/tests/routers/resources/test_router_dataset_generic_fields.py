import copy
import time
from datetime import datetime
from unittest.mock import Mock

import dateutil.parser
import pytz
from sqlalchemy.engine import Engine
from sqlmodel import Session
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.person import Person
from database.model.knowledge_asset.publication import Publication


def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset: dict,
    person: Person,
    publication: Publication,
):
    keycloak_openid.userinfo = mocked_privileged_token

    with Session(engine) as session:
        session.add(person)
        session.merge(publication)
        session.commit()

    body = copy.deepcopy(body_asset)
    body["aiod_entry"]["editor"] = [1]
    body["contact"] = [1]
    body["creator"] = [1]
    body["citation"] = [1]

    datetime_create_request = datetime.utcnow().replace(tzinfo=pytz.utc)
    response = client.post("/datasets/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/datasets/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["resource_identifier"] == 3
    assert response_json["asset_identifier"] == 2

    assert response_json["platform"] == "example"
    assert response_json["platform_identifier"] == "1"
    assert response_json["aiod_entry"]["editor"] == [1]
    assert response_json["aiod_entry"]["status"] == "draft"
    date_created = dateutil.parser.parse(response_json["aiod_entry"]["date_created"] + "Z")
    date_modified = dateutil.parser.parse(response_json["aiod_entry"]["date_modified"] + "Z")
    assert 0 < (date_created - datetime_create_request).total_seconds() < 0.1
    assert 0 < (date_modified - datetime_create_request).total_seconds() < 0.1

    assert response_json["name"] == "The name"
    assert response_json["description"] == "A description."
    assert set(response_json["alternate_name"]) == {"alias1", "alias2"}
    assert set(response_json["keyword"]) == {"tag1", "tag2"}

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
    notes = response_json["note"]
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

    body["platform_identifier"] = "2"
    body["name"] = "new name"
    body["version"] = "1.b"
    body["distribution"] = [
        {
            "name": "downloadable instance of this resource",
            "content_url": "https://www.example.com/resource_new.pdf",
        }
    ]

    time.sleep(0.5)
    datetime_update_request = datetime.utcnow().replace(tzinfo=pytz.utc)
    response = client.put("/datasets/v1/1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/datasets/v1/1")
    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["resource_identifier"] == 3
    assert response_json["asset_identifier"] == 2

    date_created = dateutil.parser.parse(response_json["aiod_entry"]["date_created"] + "Z")
    date_modified = dateutil.parser.parse(response_json["aiod_entry"]["date_modified"] + "Z")
    assert 0 < (date_created - datetime_create_request).total_seconds() < 0.1
    assert 0 < (date_modified - datetime_update_request).total_seconds() < 0.1

    assert response_json["platform"] == "example"
    assert response_json["platform_identifier"] == "2"

    assert response_json["name"] == "new name"

    (distribution,) = response_json["distribution"]
    assert distribution["name"] == "downloadable instance of this resource"
    assert distribution["content_url"] == "https://www.example.com/resource_new.pdf"

    assert response_json["version"] == "1.b"

    # TODO: test delete
