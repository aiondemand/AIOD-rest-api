import abc
from typing import Iterator


from connectors.node_names import NodeName
from database.models import CodeArtifactDescription
from schemas import CodeArtifact


class CodeArtifactConnector(abc.ABC):
    """For every node that offers datasets, this DatasetConnector should be implemented."""

    @property
    def node_name(self) -> NodeName:
        """The node of this connector"""
        return NodeName.from_class(self.__class__)

    @abc.abstractmethod
    def fetch(self, dataset: CodeArtifactDescription) -> CodeArtifact:
        """Retrieve extra metadata for this codeartifact"""
        pass

    @abc.abstractmethod
    def fetch_all(self, limit: int | None) -> Iterator[CodeArtifactDescription]:
        """Retrieve basic information of all codeartifacts"""
        pass
