from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from starlette.testclient import TestClient

from database.model.agent.agent_table import AgentTable
from database.model.agent.location import LocationORM, AddressORM, GeoORM
from database.model.ai_asset.ai_asset_table import AIAssetTable
from database.model.dataset.dataset import Dataset
from database.model.dataset.size import DatasetSizeORM


def test_happy_path(
    client: TestClient,
    engine: Engine,
):

    dataset = Dataset(
        ai_asset_identifier=AIAssetTable(type="dataset"),
        name="dataset 1",
        spatial_coverage=LocationORM(
            address=AddressORM(country="BEL"), geo=GeoORM(latitude=37.42242, longitude=-122.08585)
        ),
        size=DatasetSizeORM(unit="number of rows", value=10),
        funder=[AgentTable(type="person")],
    )

    with Session(engine) as session:
        session.add(dataset)
        session.commit()
        assert len(session.scalars(select(Dataset)).all()) == 1
        assert len(session.scalars(select(LocationORM)).all()) == 1
        assert len(session.scalars(select(AddressORM)).all()) == 1
        assert len(session.scalars(select(GeoORM)).all()) == 1
        assert len(session.scalars(select(AIAssetTable)).all()) == 1
        assert len(session.scalars(select(AgentTable)).all()) == 1
        assert len(session.scalars(select(DatasetSizeORM)).all()) == 1
        session.delete(dataset)
        session.commit()
        assert len(session.scalars(select(Dataset)).all()) == 0
        assert len(session.scalars(select(LocationORM)).all()) == 0
        assert len(session.scalars(select(AddressORM)).all()) == 0
        assert len(session.scalars(select(GeoORM)).all()) == 0
        assert len(session.scalars(select(AIAssetTable)).all()) == 0
        assert len(session.scalars(select(AgentTable)).all()) == 1
        assert len(session.scalars(select(DatasetSizeORM)).all()) == 0
