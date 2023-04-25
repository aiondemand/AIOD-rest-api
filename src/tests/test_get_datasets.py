from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.model.dataset import OrmDataset


def test_happy_path(client: TestClient, engine: Engine):
    datasets = [
        OrmDataset(
            name="dset1",
            platform="openml",
            description="a",
            same_as="openml.eu/1",
            platform_identifier="1",
        ),
        OrmDataset(
            name="dset1",
            platform="other_platform",
            description="b",
            same_as="other_platform.eu/1",
            platform_identifier="1",
        ),
        OrmDataset(
            name="dset2",
            platform="other_platform",
            description="c",
            same_as="other_platform.eu/2",
            platform_identifier="2",
        ),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(datasets)
        session.commit()

    response = client.get("/datasets/v0")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 3
    assert {ds["name"] for ds in response_json} == {"dset1", "dset2"}
    assert {ds["description"] for ds in response_json} == {"a", "b", "c"}
    assert {ds["platform"] for ds in response_json} == {"openml", "other_platform"}
    assert {ds["platform_identifier"] for ds in response_json} == {"1", "2"}
    assert {ds["identifier"] for ds in response_json} == {1, 2, 3}
    assert {ds["same_as"] for ds in response_json} == {
        "openml.eu/1",
        "other_platform.eu/1",
        "other_platform.eu/2",
    }
    for ds in response_json:
        assert len(ds) == 13
