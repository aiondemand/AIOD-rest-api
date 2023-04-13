import copy

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.model.code_artifact import OrmCodeArtifact


@pytest.mark.parametrize("codeartifact_id", [1, 2])
def test_happy_path(client: TestClient, engine: Engine, codeartifact_id: int):

    codeartifact = [
        OrmCodeArtifact(
            name="Name 1",
            doi="10.5281/zenodo.121",
            platform="zenodo",
            platform_identifier="121",
        ),
        OrmCodeArtifact(
            name="Name 2",
            doi="10.5281/zenodo.122",
            platform="zenodo",
            platform_identifier="122",
        ),
    ]
    with Session(engine) as session:
        # Populate database
        # Deepcopy necessary because SqlAlchemy changes the instance so that accessing the
        # attributes is not possible anymore
        session.add_all(copy.deepcopy(codeartifact))
        session.commit()

    response = client.get(f"/code_artifacts/{codeartifact_id}")
    assert response.status_code == 200

    response_json = response.json()

    expected = codeartifact[codeartifact_id - 1]
    assert response_json["name"] == expected.name
    assert response_json["doi"] == expected.doi
    assert response_json["platform"] == expected.platform
    assert response_json["platform_identifier"] == expected.platform_identifier
    assert response_json["identifier"] == codeartifact_id
    assert len(response_json) == 5
