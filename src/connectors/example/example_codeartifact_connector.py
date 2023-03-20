import typing


from connectors.abstract.codeartifact_connector import CodeArtifactConnector
from database.models import CodeArtifactDescription
from schemas import CodeArtifact


class ExampleCodeArtifactConnector(CodeArtifactConnector):
    def fetch(self, codeartifact: CodeArtifactDescription) -> CodeArtifact:
        return CodeArtifact(
            name=codeartifact.name,
            identifier=codeartifact.node_specific_identifier,
            doi=codeartifact.doi,
            node=codeartifact.node,
        )

    def fetch_all(self, limit: int | None) -> typing.Iterator[CodeArtifactDescription]:
        yield from [
            CodeArtifactDescription(
                name="Code 1",
                doi="doi1",
                node="example",
                node_specific_identifier="1",
            ),
            CodeArtifactDescription(
                name="Code 2",
                doi="doi2",
                node="example",
                node_specific_identifier="2",
            ),
            CodeArtifactDescription(
                name="Code 3",
                doi="doi3",
                node="example",
                node_specific_identifier="3",
            ),
            CodeArtifactDescription(
                name="Code 4",
                doi="doi4",
                node="example",
                node_specific_identifier="4",
            ),
            CodeArtifactDescription(
                name="Code 5",
                doi="doi5",
                node="example",
                node_specific_identifier="5",
            ),
        ][:limit]
