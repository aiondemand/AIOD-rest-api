from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.model.code_artifact import OrmCodeArtifact


def test_happy_path(client: TestClient, engine: Engine):
    codeartifacts = [
        OrmCodeArtifact(name="code1", doi="doi1", platform="zenodo", platform_identifier="1"),
        OrmCodeArtifact(name="code1", doi="doi1", platform="other_node", platform_identifier="1"),
        OrmCodeArtifact(name="code2", doi="doi2", platform="other_node", platform_identifier="2"),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(codeartifacts)
        session.commit()

    response = client.get("/code_artifacts")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 3
    assert {ca["name"] for ca in response_json} == {"code1", "code2"}
    assert {ca["doi"] for ca in response_json} == {"doi1", "doi2"}
    assert {ca["platform"] for ca in response_json} == {"zenodo", "other_node"}
    assert {ca["platform_identifier"] for ca in response_json} == {"1", "2"}
    assert {ca["identifier"] for ca in response_json} == {1, 2, 3}
    for ca in response_json:
        assert len(ca) == 5
