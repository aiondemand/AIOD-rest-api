from typing import Optional

from sqlmodel import Field, Column

from sqlalchemy.dialects.postgresql import JSON

from database.model.concept.concept import AIoDConceptBase, AIoDConcept
from database.model.field_length import NORMAL


class ComputationalRequirementBase(AIoDConceptBase):
    architecture: list[str] | None = Field(
        description="The underlaying design of the computer system required for the task to run.",
        sa_column=Column(JSON),
        default_factory=list,
        schema_extra={"example": ["x86_64", "ARM"]},
    )


class ComputationalRequirement(ComputationalRequirementBase, AIoDConcept, table=True):  # type: ignore [call-arg]
    """
    The computing resources required to perform a function.

    Currently, the ComputationalRequirement doesn't contain all the fields given in teh conceptual model.
    The fields are work in progress for Computational Asset.
    we will add the fields here ones they are created under ComputationAsset.
    """

    __tablename__ = "computational_requirement"
