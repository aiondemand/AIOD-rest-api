import pytest
from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from connectors import example_connectors
from database.model.dataset.dataset import Dataset
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.setup import populate_database

OPENML_URL = "https://www.openml.org/api/v1/json"
HUGGINGFACE_URL = "https://datasets-server.huggingface.co"


@pytest.mark.skip(reason="TODO: while going to Metadata model v2")
def test_example_happy_path(engine: Engine):
    with Session(engine) as session:
        session.execute(delete(Platform))  # Were added in default_sqlalchemy.clear_db()
        session.commit()
    populate_database(
        engine,
        connectors=[example_connectors["datasets"], example_connectors["publications"]],
    )
    with Session(engine) as session:
        platforms = session.scalars(select(Platform)).all()
        datasets = session.scalars(select(Dataset)).all()
        # publications = session.scalars(select(PublicationOld)).all()
        assert {p.name for p in platforms} == set(PlatformName)
        assert len(datasets) == 2
        # assert len(publications) == 20
        assert {len(d.citations) for d in datasets} == {0, 1}
        # assert {len(p.datasets) for p in publications} == {0, 1}

        (higgs_dataset,) = [d for d in datasets if d.name == "Higgs"]
        assert (
            higgs_dataset.citations[0].title == "Searching for exotic particles in high-energy "
            "physics with deep learning"
        )
