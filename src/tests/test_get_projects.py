from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient
from database.model.project import OrmProject


def test_happy_path(client: TestClient, engine: Engine):
    publications = [
        OrmProject(name="Name 1", platform="aiod", platform_identifier=None),
        OrmProject(name="Name 2", platform="aiod", platform_identifier=None),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(publications)
        session.commit()

    response = client.get("/projects/v0")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 2
    assert {pub["name"] for pub in response_json} == {"Name 1", "Name 2"}
    assert {pub["identifier"] for pub in response_json} == {1, 2}
    # assert {pub["keywords"] for pub in response_json} == {["k1"], ["k1","k2"]}
    for pub in response_json:
        assert len(pub) == 4
