from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from starlette.testclient import TestClient

from database.model.ai_asset.ai_asset_table import AIAssetTable
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication


def test_happy_path(
    client: TestClient,
    engine: Engine,
):
    dataset_distribution = Dataset.__annotations__["distribution"].__args__[0]
    publication_distribution = Publication.__annotations__["distribution"].__args__[0]
    dataset_1 = Dataset(
        name="dataset 1",
        distribution=[
            dataset_distribution(content_url="example.com/dataset1-a"),
            dataset_distribution(content_url="example.com/dataset1-b"),
        ],
        ai_asset_identifier=AIAssetTable(type="dataset"),
    )
    dataset_2 = Dataset(
        name="dataset 2",
        distribution=[
            dataset_distribution(content_url="example.com/dataset2-a"),
            dataset_distribution(content_url="example.com/dataset2-b"),
        ],
        ai_asset_identifier=AIAssetTable(type="dataset"),
    )
    publication = Publication(
        name="publication",
        distribution=[
            publication_distribution(content_url="example.com/publication1-a"),
            publication_distribution(content_url="example.com/publication1-b"),
        ],
        ai_asset_identifier=AIAssetTable(type="publication"),
    )

    with Session(engine) as session:
        session.add_all([dataset_1, dataset_2, publication])
        session.commit()
        session.delete(dataset_1)
        session.commit()
        assert len(session.scalars(select(Dataset)).all()) == 1
        assert len(session.scalars(select(Publication)).all()) == 1
        assert len(session.scalars(select(AIAssetTable)).all()) == 2
        dataset_distributions = session.scalars(select(dataset_distribution)).all()
        publication_distributions = session.scalars(select(publication_distribution)).all()
        assert {distribution.content_url for distribution in dataset_distributions} == {
            "example.com/dataset2-a",
            "example.com/dataset2-b",
        }
        assert {distribution.content_url for distribution in publication_distributions} == {
            "example.com/publication1-a",
            "example.com/publication1-b",
        }
