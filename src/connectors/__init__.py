import pathlib
from typing import Dict  # noqa:F401

from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.model.models_and_experiments.experiment import Experiment
from database.model.models_and_experiments.ml_model import MLModel
from database.model.service.service import Service
from .abstract.resource_connector import ResourceConnector  # noqa:F401
from .example.example_connector import ExampleConnector
from .huggingface.huggingface_dataset_connector import HuggingFaceDatasetConnector
from .openml.openml_dataset_connector import OpenMlDatasetConnector
from .zenodo.zenodo_dataset_connector import ZenodoDatasetConnector

dataset_connectors = {
    c.platform_name: c
    for c in (
        OpenMlDatasetConnector(),
        HuggingFaceDatasetConnector(),
        ZenodoDatasetConnector(),
    )
}

_path_example_resources = pathlib.Path(__file__).parent / "example" / "resources"

example_connectors = {
    name: ExampleConnector(
        resource_class=cls,
        json_path=_path_example_resources / f"{name}.json",
    )
    for name, cls in (
        ("datasets", Dataset),
        ("experiments", Experiment),
        ("ml_models", MLModel),
        ("organisations", Organisation),
        ("persons", Person),
        ("publications", Publication),
        ("services", Service),
    )
}  # type: Dict[str, ResourceConnector]
