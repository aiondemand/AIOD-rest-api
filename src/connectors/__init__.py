import typing  # noqa:F401


from .abstract.dataset_connector import DatasetConnector  # noqa:F401
from .abstract.publication_connector import PublicationConnector  # noqa:F401
from .abstract.codeartifact_connector import CodeArtifactConnector  # noqa:F401
from .example.example_dataset_connector import ExampleDatasetConnector
from .example.example_publication_connector import ExamplePublicationConnector
from .example.example_codeartifact_connector import ExampleCodeArtifactConnector
from .huggingface.huggingface_dataset_connector import HuggingFaceDatasetConnector
from .node_names import NodeName  # noqa:F401
from .openml.openml_dataset_connector import OpenMlDatasetConnector

dataset_connectors = {
    c.node_name: c
    for c in (ExampleDatasetConnector(), OpenMlDatasetConnector(), HuggingFaceDatasetConnector())
}  # type: typing.Dict[NodeName, DatasetConnector]

publication_connectors = {
    p.node_name: p for p in (ExamplePublicationConnector(),)
}  # type: typing.Dict[NodeName, PublicationConnector]


codeartifact_connectors = {
    c.node_name: c for c in (ExampleCodeArtifactConnector(),)
}  # type: typing.Dict[NodeName, CodeArtifactConnector]
