from pydantic import BaseModel, Field


class Dataset(BaseModel):
    """The complete metadata of a dataset. Possibly in schema.org format. For now, only a couple
    of fields are shown, we have to decide which fields to use."""

    name: str = Field(max_length=150)
    node: str = Field(max_length=30)
    node_specific_identifier: str = Field(max_length=250)
    id: int | None


class Publication(BaseModel):
    """The complete metadata of a publication. For now, only a couple of fields are shown,
    we have to decide which fields to use."""

    title: str = Field(max_length=250)
    url: str = Field(max_length=250)
    id: int | None


class CodeArtifact(BaseModel):
    """The complete metadata of a code artifact. For now, only a couple of fields are shown,
    we have to decide which fields to use."""

    name: str = Field(max_length=250)
    doi: str = Field(max_length=250)
    node: str = Field(max_length=30)
    node_specific_identifier: str = Field(max_length=250)
    id: int | None
