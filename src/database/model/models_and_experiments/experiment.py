from sqlmodel import Field, Relationship

from database.model.ai_asset.ai_asset import AIAssetBase, AIAsset
from database.model.field_length import SHORT, DESCRIPTION
from database.model.helper_functions import link_factory
from database.model.models_and_experiments.badge import Badge
from database.model.models_and_experiments.runnable_distribution import RunnableDistribution
from database.model.relationships import ResourceRelationshipList
from database.model.serializers import AttributeSerializer, FindByNameDeserializer


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
        max_length=DESCRIPTION,
        default=None,
        schema_extra={
            "example": "1) Load the dataset 2) run preprocessing code found in ... 3) "
            "run the model on the data."
        },
    )
    execution_settings: str | None = Field(
        description="A human-readable description of the settings under which the experiment was "
        "executed.",
        max_length=DESCRIPTION,
        default=None,
    )
    reproducibility_explanation: str | None = Field(
        description="A description of how the output of the experiment matches the experiments in "
        "the paper.",
        max_length=DESCRIPTION,
        default=None,
    )


class Experiment(ExperimentBase, AIAsset, table=True):  # type: ignore [call-arg]
    __tablename__ = "experiment"

    badge: list[Badge] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"},
        link_model=link_factory("experiment", Badge.__tablename__),
    )

    class RelationshipConfig(AIAsset.RelationshipConfig):
        badge: list[str] = ResourceRelationshipList(
            description="Labels awarded on the basis of the reproducibility of this experiment.",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Badge),
            default_factory_pydantic=list,
            example=["ACM Artifacts Evaluated - Reusable"],
        )
        distribution: list[RunnableDistribution] = ResourceRelationshipList(
            default_factory_pydantic=list
        )
