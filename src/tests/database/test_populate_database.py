from database.model.dataset import Dataset
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from connectors import ExampleDatasetConnector
from database.setup import populate_database

OPENML_URL = "https://www.openml.org/api/v1/json"
HUGGINGFACE_URL = "https://datasets-server.huggingface.co"


def test_example_happy_path(engine: Engine):
    populate_database(
        engine,
        connectors=[
            ExampleDatasetConnector(),
            # ExamplePublicationConnector()
        ],
    )
    with Session(engine) as session:
        datasets = session.scalars(select(Dataset)).all()
        # publications = session.scalars(select(OrmPublication)).all()
        assert len(datasets) == 2
        # assert len(publications) == 2
        # assert {len(d.citations) for d in datasets} == {0, 1}
        # assert {len(p.datasets) for p in publications} == {0, 1}

        (higgs_dataset,) = [d for d in datasets if d.name == "Higgs"]
        # assert (
        #     higgs_dataset.citations[0].title == "Searching for exotic particles in high-energy "
        #     "physics with deep learning"
        # )
