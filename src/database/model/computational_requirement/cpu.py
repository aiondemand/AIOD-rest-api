from sqlmodel import Field

from database.model.concept.concept import AIoDConcept, AIoDConceptBase
from database.model.field_length import NORMAL


class CPUBase(AIoDConceptBase):
    """
    The central processor of a computer system.
    """

    num_cpu_cores: int | None = Field(
        description="The number of cores used by the CPU.",
        default=None,
        schema_extra={"example": 6},
    )
    vendor: str | None = Field(
        description="The manufacturer of the CPU.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "AMD"},
    )
    model_name: str | None = Field(
        description="The name of the CPU model.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "Ryzen 5 3600"},
    )
    cpu_family: str | None = Field(
        description="The family in which the CPU model belongs.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "Ryzen"},
    )
    clock_speed: int | None = Field(
        description="Base clock speed of the CPU in MHz.",
        default=None,
        schema_extra={"example": 3600},
    )


class CPU(CPUBase, AIoDConcept, table=True):  # type: ignore [call-arg]
    __tablename__ = "cpu"
