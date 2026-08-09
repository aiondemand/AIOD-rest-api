from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from database.model.ai_asset.ai_asset import AIAssetBase, AIAsset
from database.model.dataset.dataset import Dataset
from database.model.field_length import SHORT, LONG
from database.model.helper_functions import many_to_many_link_factory
from database.model.models_and_experiments.badge import Badge
from database.model.models_and_experiments.runnable_distribution import RunnableDistribution
from database.model.relationships import ManyToMany, OneToMany
from database.model.serializers import (
    AttributeSerializer,
    FindByIdentifierDeserializerList,
    FindByNameDeserializerList,
)
from versioning import Version, VersionedResource, VersionedResourceCollection

if TYPE_CHECKING:
    from database.model.models_and_experiments.ml_model import MLModel


class ExperimentBase(AIAssetBase):
    pid: str | None = Field(
        description="A permanent identifier for the model, for example a digital object "
        "identifier (DOI). Ideally a url.",
        max_length=SHORT,
        default=None,
        schema_extra={"example": "https://doi.org/10.1000/182"},
    )
    experimental_workflow: str | None = Field(
        description="A human readable description of the overall workflow of the experiment.",
        max_length=LONG,
        default=None,
        schema_extra={
            "example": "1) Load the dataset 2) run preprocessing code found in ... 3) "
            "run the model on the data."
        },
    )
    execution_settings: str | None = Field(
        description="A human-readable description of the settings under which the experiment was "
        "executed.",
        max_length=LONG,
        default=None,
    )
    reproducibility_explanation: str | None = Field(
        description="A description of how the output of the experiment matches the experiments in "
        "the paper.",
        max_length=LONG,
        default=None,
    )


class Experiment(ExperimentBase, AIAsset, table=True):  # type: ignore [call-arg]
    __tablename__ = "experiment"
    __abbreviation__ = "exp"
    __plural__ = "experiments"

    badge: list[Badge] = Relationship(
        link_model=many_to_many_link_factory(
            "experiment", Badge.__tablename__, from_identifier_type=str
        ),
    )
    uses_model: list["MLModel"] = Relationship(
        link_model=many_to_many_link_factory(
            "experiment",
            "ml_model",
            table_prefix="uses_model",
            from_identifier_type=str,
            to_identifier_type=str,
        ),
    )
    uses_dataset: list[Dataset] = Relationship(
        link_model=many_to_many_link_factory(
            "experiment",
            Dataset.__tablename__,
            table_prefix="uses_dataset",
            from_identifier_type=str,
            to_identifier_type=str,
        ),
    )

    class RelationshipConfig(AIAsset.RelationshipConfig):
        badge: list[str] = ManyToMany(
            description="Labels awarded on the basis of the reproducibility of this experiment.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(Badge),
            default_factory_pydantic=list,
            example=["ACM Artifacts Evaluated - Reusable"],
        )
        distribution: list[RunnableDistribution] = OneToMany(default_factory_pydantic=list)
        uses_model: list[str] = ManyToMany(
            description="ML models used during the execution of this experiment.",
            _serializer=AttributeSerializer("identifier"),
            default_factory_pydantic=list,
            example=[],
        )
        uses_dataset: list[str] = ManyToMany(
            description="Datasets used for the execution of the experiment.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(Dataset),
            default_factory_pydantic=list,
            example=[],
        )


experiment_versions = VersionedResourceCollection(
    {
        Version.V2: VersionedResource(Experiment),
        Version.LATEST: VersionedResource(Experiment),
    }
)
