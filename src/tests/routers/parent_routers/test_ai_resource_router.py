from http import HTTPStatus

from fastapi.encoders import jsonable_encoder
from starlette.testclient import TestClient

from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.session import DbSession
from tests.testutils.users import register_asset, ALICE, logged_in_user


def test_happy_path(
    client: TestClient,
    organisation: Organisation,
    person: Person,
):

    organisation.name = "Organisation"
    person.name = "Person"
    with DbSession() as session:
        session.add(organisation)
        session.merge(person)
        session.commit()

        response = client.get(f"/ai_resources/{organisation.identifier}")
        assert response.status_code == 200, response.json()
        response_json = response.json()
        assert response_json["identifier"] == organisation.identifier
        assert response_json["ai_resource_identifier"] == organisation.identifier
        assert response_json["name"] == "Organisation"

        response = client.get(f"/ai_resources/{person.identifier}")
        assert response.status_code == 200, response.json()
        response_json = response.json()
        assert response_json["identifier"] == person.identifier
        assert response_json["ai_resource_identifier"] == person.identifier
        assert response_json["name"] == "Person"


def test_deleted_resource_not_shown_in_indirect_relationship(
        client: TestClient,
        publication_factory,
):
    pub1_id = register_asset(publication_factory(), owner=ALICE)
    with logged_in_user(ALICE):
        pub2 = publication_factory()
        response = client.post(
            f"/publications",
            json=jsonable_encoder(pub2.dict() | {"relevant_resource": [pub1_id]}),
            headers={"Authorization": "fake token"}
        )
        assert response.status_code == HTTPStatus.OK
        pub2_id = response.json()["identifier"]

        response = client.get(f"/publications/{pub1_id}")
        assert response.status_code == HTTPStatus.OK
        assert pub2_id in response.json()["relevant_to"]

        response = client.delete(
            f"/publications/{pub2_id}",
            headers={"Authorization": "fake token"}
        )
        assert response.status_code == HTTPStatus.OK

        response = client.get(f"/publications/{pub1_id}")
        assert response.status_code == HTTPStatus.OK
        assert pub2_id not in response.json()["relevant_to"], "Related resources should ignore soft-deleted assets"


def test_deleted_resource_not_shown_in_direct_relationship(
        client: TestClient,
        organisation,
        person,
):
    org_id = register_asset(organisation, owner=ALICE)
    with logged_in_user(ALICE):
        response = client.post(
            f"/persons",
            json=jsonable_encoder(person.dict() | {"member_of": [org_id]}),
            headers={"Authorization": "fake token"}
        )
        assert response.status_code == HTTPStatus.OK
        person_id = response.json()["identifier"]

        response = client.get(
            f"/persons/{person_id}",
            headers={"Authorization": "fake token"}
        )
        assert response.status_code == HTTPStatus.OK
        assert org_id in response.json()["member_of"]

        response = client.delete(
            f"/organisations/{org_id}",
            headers={"Authorization": "fake token"}
        )
        assert response.status_code == HTTPStatus.OK

        response = client.get(
            f"/persons/{person_id}",
            headers={"Authorization": "fake token"}
        )
        assert response.status_code == HTTPStatus.OK
        assert org_id not in response.json()["member_of"], "Direct relationships should ignore soft-deleted assets"
