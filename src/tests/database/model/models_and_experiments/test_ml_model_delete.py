from sqlmodel import select
from starlette.testclient import TestClient

from database.model.models_and_experiments.experiment import Experiment
from database.model.models_and_experiments.ml_model import MLModel
from database.session import DbSession


def test_happy_path(client: TestClient):
    experiment = Experiment(name="experiment")
    ml_model = MLModel(name="model", related_experiment=[experiment])
    link_model = ml_model.__sqlmodel_relationships__["related_experiment"].link_model

    with DbSession() as session:
        session.add(ml_model)
        session.commit()
        assert len(session.scalars(select(Experiment)).all()) == 1
        assert len(session.scalars(select(MLModel)).all()) == 1
        assert len(session.scalars(select(link_model)).all()) == 1
        session.delete(ml_model)
        session.commit()
        assert len(session.scalars(select(Experiment)).all()) == 1
        assert len(session.scalars(select(MLModel)).all()) == 0
        assert len(session.scalars(select(link_model)).all()) == 0
