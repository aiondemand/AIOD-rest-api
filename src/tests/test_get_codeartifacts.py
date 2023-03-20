from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.models import CodeArtifactDescription


def test_happy_path(client: TestClient, engine: Engine):
    codeartifacts = [
        CodeArtifactDescription(
            name="code1", doi="doi1", node="zenodo", node_specific_identifier="1"
        ),
        CodeArtifactDescription(
            name="code1", doi="doi1", node="other_node", node_specific_identifier="1"
        ),
        CodeArtifactDescription(
            name="code2", doi="doi2", node="other_node", node_specific_identifier="2"
        ),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(codeartifacts)
        session.commit()

    response = client.get("/codeartifacts")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 3
    assert {ca["name"] for ca in response_json} == {"code1", "code2"}
    assert {ca["doi"] for ca in response_json} == {"doi1", "doi2"}
    assert {ca["node"] for ca in response_json} == {"zenodo", "other_node"}
    assert {ca["node_specific_identifier"] for ca in response_json} == {"1", "2"}
    assert {ca["id"] for ca in response_json} == {1, 2, 3}
    for ca in response_json:
        assert len(ca) == 5
